"""Public report CLI over synthetic local histories; no real session data."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/skill-usage-report/scripts/report.py"


class UsageReportCLI(unittest.TestCase):
    def test_system_skill_and_all_scope_are_visible_without_double_counting(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            codex = root / "codex"
            codex.mkdir()
            claude = root / "claude"
            projects = claude / "projects/fixture"
            projects.mkdir(parents=True)
            rollout = codex / "rollout.jsonl"
            start = 1791378000
            records = [
                {"timestamp": start, "type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn"}},
                {"timestamp": start + 1, "type": "response_item", "payload": {"type": "function_call", "arguments": 'cat /fixture/.codex/skills/.system/skill-creator/SKILL.md'}},
                {"timestamp": start + 2, "type": "response_item", "payload": {"type": "function_call", "arguments": 'cat /fixture/.codex/skills/.system/skill-creator/SKILL.md'}},
                {"timestamp": start + 3, "type": "token_usage_record", "payload": {"turn_id": "turn", "response_id": "response", "usage": {"total_tokens": 42}}},
            ]
            rollout.write_text("\n".join(json.dumps(row) for row in records))
            with sqlite3.connect(codex / "state_5.sqlite") as db:
                db.execute("CREATE TABLE threads (id,rollout_path,cwd,git_origin_url,updated_at,created_at)")
                db.execute("CREATE TABLE thread_spawn_edges (child_thread_id,parent_thread_id)")
                db.execute("INSERT INTO threads VALUES (?,?,?,?,?,?)", ("task", str(rollout), "/fixture/documents", None, start + 10, start))
            with sqlite3.connect(codex / "thread_history_1.sqlite") as db:
                db.execute("CREATE TABLE thread_turns (thread_id,turn_id,started_at,completed_at)")
                db.execute("INSERT INTO thread_turns VALUES (?,?,?,?)", ("task", "turn", start, start + 10))
            (projects / "session.jsonl").write_text("\n".join(json.dumps(row) for row in [
                {"type": "user", "timestamp": start, "cwd": "/fixture/documents", "message": {"content": "Make a document"}},
                {"type": "assistant", "timestamp": start + 1, "message": {"id": "message", "content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "documents"}}]}},
                {"type": "assistant", "timestamp": start + 5, "message": {"id": "result", "usage": {"input_tokens": 7, "output_tokens": 3}, "content": []}},
            ]))
            output = root / "report.json"
            command = [sys.executable, str(SCRIPT), "--from", "2026-10-07", "--to", "2026-10-07", "--codex-home", str(codex), "--claude-home", str(claude), "--json", str(output)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text())["skills"], {})
            result = subprocess.run(command + ["--all"], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(output.read_text())
            self.assertEqual(data["scope"], "all")
            self.assertEqual(data["skills"]["skill-creator"]["uses"], 1)
            self.assertEqual(data["skills"]["skill-creator"]["tokens"], 42)
            self.assertEqual(data["skills"]["documents"]["tokens"], 10)
            self.assertIn("во всех задачах", result.stdout)
