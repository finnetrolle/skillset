#!/usr/bin/env python3
"""Audit and safely link user-managed skills across agent hosts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


IGNORED_FILES = {".DS_Store"}
IGNORED_DIRECTORIES = {".git", "__pycache__"}
CLAUDE_FRONTMATTER_MARKERS = {
    "agent",
    "argument-hint",
    "background",
    "context",
    "disable-model-invocation",
    "disallowed-tools",
    "effort",
    "hooks",
    "model",
    "paths",
    "shell",
    "user-invocable",
}


@dataclass(frozen=True)
class SkillEntry:
    """Describe one skill directory discovered in a host root."""

    host: str
    root: str
    directory_name: str
    normalized_name: str
    declared_name: str | None
    path: str
    resolved_path: str
    digest: str
    markers: tuple[str, ...]


@dataclass(frozen=True)
class Diagnostic:
    """Describe an invalid or suspicious inventory entry."""

    host: str
    path: str
    message: str


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    """Return absolute paths in input order with textual duplicates removed."""

    result: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        expanded = path.expanduser().absolute()
        key = os.path.normcase(str(expanded))
        if key not in seen:
            seen.add(key)
            result.append(expanded)
    return result


def default_codex_roots() -> list[Path]:
    """Return current and legacy personal Codex skill roots."""

    home = Path.home()
    configured_home = Path(os.environ.get("CODEX_HOME", home / ".codex"))
    return unique_paths([home / ".agents" / "skills", configured_home / "skills"])


def default_claude_roots() -> list[Path]:
    """Return the personal Claude Code skill root."""

    return [Path.home() / ".claude" / "skills"]


def unquote_yaml_scalar(value: str) -> str:
    """Remove simple matching YAML quotes from a scalar value."""

    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1]
    return stripped


def parse_frontmatter(text: str) -> tuple[dict[str, str], bool]:
    """Parse top-level scalar keys from a SKILL.md YAML frontmatter block."""

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, False
    closing = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if closing is None:
        return {}, False

    values: dict[str, str] = {}
    for line in lines[1:closing]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1)] = unquote_yaml_scalar(match.group(2))
    return values, True


def hash_skill_directory(skill_dir: Path) -> str:
    """Hash stable relative paths and file contents under a skill directory."""

    digest = hashlib.sha256()
    resolved_root = skill_dir.resolve(strict=True)
    for current_root, directory_names, file_names in os.walk(resolved_root, followlinks=False):
        directory_names[:] = sorted(
            name for name in directory_names if name not in IGNORED_DIRECTORIES
        )
        current = Path(current_root)
        for file_name in sorted(file_names):
            if file_name in IGNORED_FILES or file_name.endswith(".pyc"):
                continue
            file_path = current / file_name
            relative = file_path.relative_to(resolved_root).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            if file_path.is_symlink():
                digest.update(b"symlink\0")
                digest.update(os.readlink(file_path).encode("utf-8"))
            else:
                digest.update(b"file\0")
                with file_path.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
            digest.update(b"\0")
    return digest.hexdigest()


def portability_markers(skill_dir: Path, text: str, frontmatter: dict[str, str]) -> tuple[str, ...]:
    """Return host-specific constructs that deserve review before merging."""

    markers: set[str] = set()
    if (skill_dir / "agents" / "openai.yaml").exists():
        markers.add("codex-ui-metadata")
    if "${CLAUDE_" in text or "$ARGUMENTS" in text:
        markers.add("claude-placeholders")
    if re.search(r"(?m)^\s*!`", text):
        markers.add("claude-dynamic-command")
    if CLAUDE_FRONTMATTER_MARKERS.intersection(frontmatter):
        markers.add("claude-frontmatter")
    if "${CODEX_" in text or "::code-comment" in text:
        markers.add("codex-directive")
    return tuple(sorted(markers))


def discover_skills(host: str, roots: Sequence[Path]) -> tuple[list[SkillEntry], list[Diagnostic]]:
    """Discover direct child skill directories from the supplied host roots."""

    entries: list[SkillEntry] = []
    diagnostics: list[Diagnostic] = []
    for root in roots:
        if not root.exists():
            diagnostics.append(Diagnostic(host, str(root), "root does not exist"))
            continue
        if not root.is_dir():
            diagnostics.append(Diagnostic(host, str(root), "root is not a directory"))
            continue

        for candidate in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
            directory_name = candidate.name
            if directory_name.startswith("."):
                continue
            if host == "claude" and directory_name.casefold() == "synced":
                continue
            if candidate.is_symlink() and not candidate.exists():
                diagnostics.append(Diagnostic(host, str(candidate), "broken skill symlink"))
                continue
            if not candidate.is_dir():
                continue

            skill_file = candidate / "SKILL.md"
            if not skill_file.is_file():
                continue
            try:
                text = skill_file.read_text(encoding="utf-8")
                frontmatter, has_frontmatter = parse_frontmatter(text)
                declared_name = frontmatter.get("name") or None
                digest = hash_skill_directory(candidate)
            except (OSError, UnicodeError) as error:
                diagnostics.append(Diagnostic(host, str(candidate), f"cannot read skill: {error}"))
                continue

            if not has_frontmatter:
                diagnostics.append(Diagnostic(host, str(skill_file), "missing or unterminated YAML frontmatter"))
            if not frontmatter.get("description"):
                diagnostics.append(Diagnostic(host, str(skill_file), "frontmatter has no scalar description"))
            if declared_name and declared_name.casefold() != directory_name.casefold():
                diagnostics.append(
                    Diagnostic(host, str(skill_file), f"declared name '{declared_name}' differs from directory name")
                )

            entries.append(
                SkillEntry(
                    host=host,
                    root=str(root),
                    directory_name=directory_name,
                    normalized_name=directory_name.casefold(),
                    declared_name=declared_name,
                    path=str(candidate),
                    resolved_path=str(candidate.resolve()),
                    digest=digest,
                    markers=portability_markers(candidate, text, frontmatter),
                )
            )
    return entries, diagnostics


def group_by_name(entries: Sequence[SkillEntry]) -> dict[str, list[SkillEntry]]:
    """Group inventory entries by case-insensitive directory name."""

    grouped: dict[str, list[SkillEntry]] = {}
    for entry in entries:
        grouped.setdefault(entry.normalized_name, []).append(entry)
    return grouped


def side_is_ambiguous(entries: Sequence[SkillEntry]) -> bool:
    """Return whether one host exposes different contents under the same name."""

    return len({entry.digest for entry in entries}) > 1


def comparison_rows(
    codex_entries: Sequence[SkillEntry], claude_entries: Sequence[SkillEntry]
) -> list[dict[str, object]]:
    """Build cross-host comparison rows from inventory entries."""

    codex = group_by_name(codex_entries)
    claude = group_by_name(claude_entries)
    rows: list[dict[str, object]] = []
    for normalized_name in sorted(set(codex) | set(claude)):
        left = codex.get(normalized_name, [])
        right = claude.get(normalized_name, [])
        notes: list[str] = []

        if left and side_is_ambiguous(left):
            state = "ambiguous-codex"
        elif right and side_is_ambiguous(right):
            state = "ambiguous-claude"
        elif not left:
            state = "claude-only"
        elif not right:
            state = "codex-only"
        elif left[0].digest == right[0].digest:
            state = "identical"
        else:
            state = "different"

        if len(left) > 1 and not side_is_ambiguous(left):
            notes.append("duplicate identical Codex entries")
        if len(right) > 1 and not side_is_ambiguous(right):
            notes.append("duplicate identical Claude entries")
        markers = sorted({marker for entry in [*left, *right] for marker in entry.markers})
        if markers:
            notes.append("markers: " + ", ".join(markers))

        display_name = (left or right)[0].directory_name
        rows.append(
            {
                "name": display_name,
                "normalized_name": normalized_name,
                "state": state,
                "codex": [asdict(entry) for entry in left],
                "claude": [asdict(entry) for entry in right],
                "notes": notes,
            }
        )
    return rows


def inventory(codex_roots: Sequence[Path], claude_roots: Sequence[Path]) -> dict[str, object]:
    """Return the complete cross-host inventory report."""

    codex_entries, codex_diagnostics = discover_skills("codex", codex_roots)
    claude_entries, claude_diagnostics = discover_skills("claude", claude_roots)
    rows = comparison_rows(codex_entries, claude_entries)
    counts: dict[str, int] = {}
    for row in rows:
        state = str(row["state"])
        counts[state] = counts.get(state, 0) + 1
    return {
        "roots": {
            "codex": [str(path) for path in codex_roots],
            "claude": [str(path) for path in claude_roots],
        },
        "exclusions": ["hidden directories", "Codex .system", "Claude synced"],
        "counts": counts,
        "skills": rows,
        "diagnostics": [asdict(item) for item in [*codex_diagnostics, *claude_diagnostics]],
    }


def compact_locations(entries: Sequence[dict[str, object]]) -> str:
    """Format entry paths for a Markdown table cell."""

    if not entries:
        return "-"
    return "<br>".join(f"`{entry['path']}`" for entry in entries)


def render_markdown(report: dict[str, object]) -> str:
    """Render an inventory report as Markdown."""

    roots = report["roots"]
    assert isinstance(roots, dict)
    lines = ["# Skill inventory", "", "## Scope", ""]
    lines.append("- Codex roots: " + ", ".join(f"`{root}`" for root in roots["codex"]))
    lines.append("- Claude roots: " + ", ".join(f"`{root}`" for root in roots["claude"]))
    lines.append("- Exclusions: " + ", ".join(report["exclusions"]))
    lines.extend(["", "## Comparison", "", "| Skill | State | Codex | Claude Code | Notes |", "| --- | --- | --- | --- | --- |"])
    for row in report["skills"]:
        notes = "; ".join(row["notes"]) or "-"
        lines.append(
            f"| `{row['name']}` | `{row['state']}` | {compact_locations(row['codex'])} | "
            f"{compact_locations(row['claude'])} | {notes} |"
        )

    lines.extend(["", "## Summary", ""])
    counts = report["counts"]
    if counts:
        for state in sorted(counts):
            lines.append(f"- `{state}`: {counts[state]}")
    else:
        lines.append("- No skills found.")

    diagnostics = report["diagnostics"]
    if diagnostics:
        lines.extend(["", "## Diagnostics", ""])
        for item in diagnostics:
            lines.append(f"- `{item['host']}` `{item['path']}`: {item['message']}")
    return "\n".join(lines)


def link_operations(
    report: dict[str, object], codex_target: Path, claude_target: Path
) -> tuple[list[dict[str, str]], list[str]]:
    """Build non-overwriting symlink operations for skills absent from one host."""

    operations: list[dict[str, str]] = []
    blockers: list[str] = []
    for row in report["skills"]:
        state = row["state"]
        if state == "codex-only":
            source = Path(row["codex"][0]["resolved_path"])
            destination = claude_target / row["name"]
        elif state == "claude-only":
            source = Path(row["claude"][0]["resolved_path"])
            destination = codex_target / row["name"]
        elif state in {"different", "ambiguous-codex", "ambiguous-claude"}:
            blockers.append(f"{row['name']}: {state}")
            continue
        else:
            continue

        if os.path.lexists(destination):
            blockers.append(f"{row['name']}: destination already exists at {destination}")
            continue
        operations.append({"source": str(source), "destination": str(destination)})
    return operations, blockers


def apply_links(operations: Sequence[dict[str, str]]) -> None:
    """Create planned skill symlinks without overwriting any path."""

    for operation in operations:
        source = Path(operation["source"])
        destination = Path(operation["destination"])
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            raise RuntimeError(f"source is no longer a valid skill: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if os.path.lexists(destination):
            raise RuntimeError(f"refusing to overwrite existing destination: {destination}")
        destination.symlink_to(source, target_is_directory=True)


def resolve_roots(arguments: argparse.Namespace) -> tuple[list[Path], list[Path]]:
    """Resolve CLI roots, using host defaults when no override was supplied."""

    codex = (
        unique_paths(Path(value) for value in arguments.codex_root)
        if arguments.codex_root
        else default_codex_roots()
    )
    claude = (
        unique_paths(Path(value) for value in arguments.claude_root)
        if arguments.claude_root
        else default_claude_roots()
    )
    return codex, claude


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_roots(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--codex-root", action="append", default=[], help="Codex skill root; repeat to include more than one"
        )
        subparser.add_argument(
            "--claude-root", action="append", default=[], help="Claude Code skill root; repeat to include more than one"
        )

    audit = subparsers.add_parser("audit", help="compare skill names and content")
    add_roots(audit)
    audit.add_argument("--format", choices=("markdown", "json"), default="markdown")

    link = subparsers.add_parser(
        "link-missing", help="preview or create links for skills missing from one host"
    )
    add_roots(link)
    link.add_argument("--apply", action="store_true", help="create the planned links; default is a dry run")
    link.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested inventory command."""

    arguments = build_parser().parse_args(argv)
    codex_roots, claude_roots = resolve_roots(arguments)
    report = inventory(codex_roots, claude_roots)

    if arguments.command == "audit":
        output = (
            json.dumps(report, indent=2, ensure_ascii=False)
            if arguments.format == "json"
            else render_markdown(report)
        )
        print(output)
        return 0

    operations, blockers = link_operations(report, codex_roots[0], claude_roots[0])
    result = {
        "mode": "apply" if arguments.apply else "dry-run",
        "operations": operations,
        "blockers": blockers,
    }
    if arguments.apply:
        try:
            apply_links(operations)
        except (OSError, RuntimeError) as error:
            print(f"linking failed: {error}", file=sys.stderr)
            return 2

    if arguments.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Mode: {result['mode']}")
        if operations:
            for operation in operations:
                verb = "linked" if arguments.apply else "would link"
                print(f"- {verb}: {operation['destination']} -> {operation['source']}")
        else:
            print("- No missing skills can be linked safely.")
        if blockers:
            print("Blockers requiring review:")
            for blocker in blockers:
                print(f"- {blocker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
