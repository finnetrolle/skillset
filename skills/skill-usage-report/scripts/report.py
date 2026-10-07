#!/usr/bin/env python3
"""Read local Codex and Claude Code histories; report skill-associated usage."""

import argparse
import bisect
import collections
import datetime as dt
import json
from pathlib import Path
import re
import sqlite3
from zoneinfo import ZoneInfo

SKILL_PATH = re.compile(r"(?P<path>(?:/|~[/\\])[^\s\"']*[/\\]skills[/\\](?:\.system[/\\])?(?P<name>[a-z][a-z0-9-]*)[/\\]SKILL\.md)\b", re.I)
READ_VERB = re.compile(r"\b(cat|sed|head|tail|less|more|read_text|read_file|Get-Content|Read)\b", re.I)


def instant(value):
    if isinstance(value, (int, float)):
        return float(value)
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return None


def skill_reads(value, direct=False):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    result = []
    for match in SKILL_PATH.finditer(text):
        path = match.group("path")
        if not any(x in path for x in ("/.codex/skills/", "/.claude/skills/", "/.agents/skills/",
                                       "/.codex/plugins/cache/")):
            continue
        if direct or READ_VERB.search(text[max(0, match.start() - 160):match.start()]):
            result.append(match.group("name").lower())
    return result


def is_dev(cwd, git_origin, roots):
    if git_origin:
        return True
    if not cwd:
        return False
    p = Path(cwd).expanduser()
    return any(p == root or root in p.parents for root in roots)


def usage_tokens(usage, source):
    if not isinstance(usage, dict):
        return None
    if source == "Codex":
        return usage.get("total_tokens")
    fields = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
    if not any(k in usage for k in fields):
        return None
    return sum(int(usage.get(k) or 0) for k in fields)


class Report:
    def __init__(self):
        self.rows = collections.defaultdict(lambda: {"uses": 0, "tasks": set(), "tokens": 0,
                                                    "seconds": 0.0, "sources": set(), "missing_tokens": 0,
                                                    "missing_time": 0})
        self.coverage = collections.Counter()
        self.warnings = []

    def add_turn(self, source, task, activations, usages, end, started):
        self.coverage[source + " turns"] += 1
        if not activations:
            return
        self.coverage[source + " turns with skills"] += 1
        activations.sort()
        phases = []
        seen = set()
        for when, skill in activations:
            if skill not in seen:
                self.rows[skill]["uses"] += 1
                self.rows[skill]["tasks"].add((source, task))
                self.rows[skill]["sources"].add(source)
                seen.add(skill)
            if phases and phases[-1][1] == skill:
                continue
            phases.append((when, skill))
        if not end:
            end = max([started] + [x[0] for x in phases] + [x[0] for x in usages])
            self.coverage["unfinished turns"] += 1
        for i, (when, skill) in enumerate(phases):
            until = phases[i + 1][0] if i + 1 < len(phases) else end
            row = self.rows[skill]
            if until >= when:
                row["seconds"] += until - when
            else:
                row["missing_time"] += 1
            if not any(when <= used_at < until for used_at, _ in usages):
                row["missing_tokens"] += 1
        for when, tokens in usages:
            i = bisect.bisect_right(phases, (when, "\uffff")) - 1
            if i < 0 or when > end:
                continue
            row = self.rows[phases[i][1]]
            if tokens is None:
                row["missing_tokens"] += 1
            else:
                row["tokens"] += tokens


def codex(report, codex_home, start, stop, roots, all_tasks=False):
    state = codex_home / "state_5.sqlite"
    history = codex_home / "thread_history_1.sqlite"
    if not state.is_file() or not history.is_file():
        report.warnings.append("База Codex недоступна")
        return
    try:
        s = sqlite3.connect(f"file:{state}?mode=ro", uri=True)
        h = sqlite3.connect(f"file:{history}?mode=ro", uri=True)
        threads = s.execute("SELECT id,rollout_path,cwd,git_origin_url FROM threads "
                            "WHERE updated_at>=? AND created_at<?", (int(start), int(stop))).fetchall()
        parents = dict(s.execute("SELECT child_thread_id,parent_thread_id FROM thread_spawn_edges"))
        for thread_id, path, cwd, remote in threads:
            if not all_tasks and not is_dev(cwd, remote, roots):
                continue
            turns = {tid: (started, completed) for tid, started, completed in h.execute(
                "SELECT turn_id,started_at,completed_at FROM thread_turns "
                "WHERE thread_id=? AND started_at>=? AND started_at<?",
                (thread_id, int(start), int(stop)))}
            if not turns:
                continue
            report.coverage["Codex files selected"] += 1
            activations = collections.defaultdict(list)
            usages = collections.defaultdict(list)
            current = None
            seen_responses = set()
            try:
                with open(path, encoding="utf-8", errors="replace") as file:
                    for line in file:
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        payload = record.get("payload") or {}
                        kind = record.get("type")
                        if kind == "event_msg" and payload.get("type") == "task_started":
                            current = payload.get("turn_id")
                        if current not in turns and kind != "token_usage_record":
                            continue
                        when = instant(record.get("timestamp"))
                        if when is None:
                            continue
                        if kind == "response_item" and payload.get("type") in ("custom_tool_call", "function_call"):
                            inp = payload.get("input") or payload.get("arguments") or ""
                            for skill in skill_reads(inp):
                                activations[current].append((when, skill))
                        elif kind == "token_usage_record":
                            turn_id = payload.get("turn_id")
                            response_id = payload.get("response_id")
                            key = (turn_id, response_id)
                            if turn_id in turns and key not in seen_responses:
                                seen_responses.add(key)
                                usages[turn_id].append((when, usage_tokens(payload.get("usage"), "Codex")))
            except (OSError, UnicodeError):
                report.coverage["Codex files unreadable"] += 1
                continue
            task = thread_id
            visited = set()
            while task in parents and task not in visited:
                visited.add(task)
                task = parents[task]
            for turn_id, (started, completed) in turns.items():
                report.add_turn("Codex", task, activations[turn_id], usages[turn_id],
                                instant(completed), instant(started))
        s.close()
        h.close()
    except sqlite3.Error as error:
        report.warnings.append(f"Ошибка чтения базы Codex: {error}")


def human_prompt(record):
    if record.get("type") != "user" or record.get("isMeta"):
        return False
    content = (record.get("message") or {}).get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        return any(isinstance(x, dict) and x.get("type") == "text" and x.get("text", "").strip()
                   for x in content)
    return False


def claude(report, claude_home, start, stop, roots, all_tasks=False):
    projects = claude_home / "projects"
    if not projects.is_dir():
        report.warnings.append("Журналы Claude Code недоступны")
        return
    for path in projects.glob("**/*.jsonl"):
        try:
            if path.stat().st_mtime < start:
                continue
        except OSError:
            continue
        task = path.parent.parent.name if path.parent.name == "subagents" else path.stem
        turn = None
        cwd = None
        def flush():
            if turn and (all_tasks or is_dev(cwd, None, roots)) and start <= turn["start"] < stop:
                report.add_turn("Claude Code", task, turn["skills"],
                                [(v[0], v[1]) for v in turn["messages"].values()],
                                turn["last"], turn["start"])
        try:
            with path.open(encoding="utf-8", errors="replace") as file:
                for line in file:
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    when = instant(item.get("timestamp"))
                    if when is None or when >= stop:
                        continue
                    cwd = item.get("cwd") or cwd
                    if human_prompt(item):
                        flush()
                        turn = {"start": when, "last": when, "skills": [], "messages": {}}
                    if turn is None or when < turn["start"] or when < start:
                        continue
                    if item.get("type") not in ("assistant", "user"):
                        continue
                    turn["last"] = max(turn["last"], when)
                    if item.get("type") != "assistant":
                        continue
                    message = item.get("message") or {}
                    message_id = message.get("id")
                    tokens = usage_tokens(message.get("usage"), "Claude Code")
                    if message_id and tokens is not None:
                        old = turn["messages"].get(message_id)
                        if old is None or tokens > old[1]:
                            turn["messages"][message_id] = (when, tokens)
                    for block in message.get("content") or []:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        name, inp = block.get("name"), block.get("input") or {}
                        if name == "Skill" and isinstance(inp, dict) and inp.get("skill"):
                            turn["skills"].append((when, inp["skill"].lower()))
                        elif name == "Read":
                            turn["skills"].extend((when, x) for x in skill_reads(inp, direct=True))
                        elif name == "Bash":
                            turn["skills"].extend((when, x) for x in skill_reads(inp))
            flush()
            report.coverage["Claude Code files selected"] += 1
        except (OSError, UnicodeError):
            report.coverage["Claude Code files unreadable"] += 1


def fmt_time(seconds):
    if seconds < 3600:
        return f"{seconds / 60:.0f} мин"
    return f"{seconds / 3600:.1f} ч"


def markdown(report, start, stop, tz, all_tasks=False):
    scope = "во всех задачах" if all_tasks else "в задачах разработки"
    lines = [f"# Использование скиллов {scope}", "",
             f"Период: {dt.datetime.fromtimestamp(start, tz):%d.%m.%Y %H:%M} - "
             f"{dt.datetime.fromtimestamp(stop, tz):%d.%m.%Y %H:%M} ({tz.key}).", "",
             "| Скилл | Применений | Задач | Токенов после активации | Время после активации | Токенов/применение | Мин/применение | Источник |",
             "|---|---:|---:|---:|---:|---:|---:|---|"]
    for skill, row in sorted(report.rows.items(), key=lambda x: (-x[1]["uses"], x[0])):
        uses = row["uses"]
        token = f"{row['tokens']:,}".replace(",", " ") if row["tokens"] else ("н/д" if row["missing_tokens"] else "0")
        per = f"{row['tokens'] / uses:,.0f}".replace(",", " ") if row["tokens"] else ("н/д" if row["missing_tokens"] else "0")
        lines.append(f"| `{skill}` | {uses} | {len(row['tasks'])} | {token} | {fmt_time(row['seconds'])} | {per} | {row['seconds']/60/uses:.0f} | {', '.join(sorted(row['sources']))} |")
    if not report.rows:
        lines.append("| Скиллы с подтверждённым применением не найдены | 0 | 0 | н/д | н/д | н/д | н/д | - |")
    lines += ["", "## Покрытие и интерпретация", ""]
    for source in ("Codex", "Claude Code"):
        lines.append(f"- {source}: {report.coverage[source + ' turns']} ходов, "
                     f"{report.coverage[source + ' turns with skills']} со скиллами.")
    if report.coverage["unfinished turns"]:
        lines.append(f"- Незавершённых ходов: {report.coverage['unfinished turns']}; их время и токены частичны.")
    missing = sum(row["missing_tokens"] for row in report.rows.values())
    if missing:
        lines.append(f"- Для {missing} этапов нет записей usage после активации; их токены не включены в суммы.")
    if report.coverage["Codex files unreadable"] or report.coverage["Claude Code files unreadable"]:
        lines.append("- Часть файлов не прочитана; покрытие неполное.")
    lines.append("- Применение подтверждено вызовом `Skill` или чтением конкретного `SKILL.md`. "
                 "Автоматически подгруженные инструкции без такого следа могут отсутствовать.")
    lines.append("- Токены и время относятся к этапу после активации до следующего скилла или конца хода. "
                 "Это оценка связи с работой, а не изолированная стоимость скилла. Время включает ожидания; "
                 "суммы параллельных задач не равны рабочему времени человека.")
    lines.append("- По этим данным нельзя доказать экономию относительно выполнения тех же задач без скилла.")
    for warning in report.warnings:
        lines.append(f"- {warning}.")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--from", dest="date_from", help="YYYY-MM-DD, включительно")
    p.add_argument("--to", dest="date_to", help="YYYY-MM-DD, включительно")
    p.add_argument("--tz", default="Europe/Moscow")
    p.add_argument("--dev-root", action="append", help="Дополнительный корень проектов; повторяемый параметр")
    p.add_argument("--all", action="store_true", dest="all_tasks", help="Все задачи, включая работу вне репозиториев")
    p.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    p.add_argument("--claude-home", type=Path, default=Path.home() / ".claude")
    p.add_argument("--output", type=Path)
    p.add_argument("--json", type=Path)
    args = p.parse_args()
    if args.days < 1:
        p.error("--days должен быть положительным")
    try:
        tz = ZoneInfo(args.tz)
    except KeyError:
        p.error("неизвестный часовой пояс")
    now = dt.datetime.now(tz)
    start = dt.datetime.combine(dt.date.fromisoformat(args.date_from), dt.time(), tz).timestamp() if args.date_from else (now - dt.timedelta(days=args.days)).timestamp()
    stop = dt.datetime.combine(dt.date.fromisoformat(args.date_to) + dt.timedelta(days=1), dt.time(), tz).timestamp() if args.date_to else now.timestamp()
    if start >= stop:
        p.error("начало периода должно быть раньше конца")
    roots = [Path(x).expanduser().resolve() for x in
             (["~/dev", "~/.no-mistakes/worktrees"] + (args.dev_root or []))]
    report = Report()
    codex(report, args.codex_home.expanduser(), start, stop, roots, args.all_tasks)
    claude(report, args.claude_home.expanduser(), start, stop, roots, args.all_tasks)
    result = markdown(report, start, stop, tz, args.all_tasks)
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    if args.json:
        data = {"start": start, "stop": stop, "timezone": tz.key, "scope": "all" if args.all_tasks else "development", "coverage": dict(report.coverage),
                "warnings": report.warnings,
                "skills": {k: {**v, "tasks": len(v["tasks"]), "sources": sorted(v["sources"])}
                           for k, v in sorted(report.rows.items())}}
        args.json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
