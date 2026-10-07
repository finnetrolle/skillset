#!/usr/bin/env python3
"""Validate a WORK_ITEMS-style Markdown backlog and print its work frontier."""

from __future__ import annotations

import argparse
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse


ID_PATTERN = re.compile(r"\b(?:EPIC|VIG)-[A-Z0-9-]+\b")
STATUS_PATTERN = re.compile(r"^\*\*(?:Статус|Status):\*\*\s*(.+?)\s*$", re.MULTILINE)
EXPLICIT_ID_PATTERN = re.compile(r"^\*\*ID:\*\*\s*`?([^`\s]+)`?\s*$", re.MULTILINE)
DEPENDENCY_PATTERN = re.compile(r"^\*\*(?:Зависит от|Blocked by):\*\*\s*(.+?)\s*$", re.MULTILINE)
PARENT_PATTERN = re.compile(r"^\*\*(?:Epic|Эпик):\*\*\s*(.+?)\s*$", re.MULTILINE)
CHECKLIST_PATTERN = re.compile(
    r"^- \[([ xX])\] \[((?:EPIC|VIG)-[A-Z0-9-]+)(?::[^\]]*)?\]"
    r"\(([^)]+)\)\s+-\s+`([^`]+)`\s*$",
    re.MULTILINE,
)
REGISTRY_PATTERN = re.compile(
    r"^\|\s*\[((?:EPIC|VIG)-[A-Z0-9-]+)(?::[^\]]*)?\]\(([^)]+)\)"
    r"\s*\|\s*`([^`]+)`\s*\|\s*(\d+)/(\d+)\s*\|",
    re.MULTILINE,
)
MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
ALLOWED_STATUSES = {
    "Draft",
    "Ready for implementation",
    "In progress",
    "Blocked",
    "Done",
}


@dataclass(frozen=True)
class WorkItem:
    item_id: str
    status: str
    blockers: tuple[str, ...]
    parent_id: str | None
    path: Path


@dataclass(frozen=True)
class ValidationReport:
    errors: list[str]
    frontier: list[str]
    item_count: int


def validate_repository(root: Path) -> ValidationReport:
    """Return structural errors and currently grabbable issues for a repository."""
    spec = root.resolve() / "spec"
    paths = sorted((spec / "epics").glob("*.md"))
    paths.extend(sorted((spec / "issues").glob("**/*.md")))
    items: list[WorkItem] = []
    errors: list[str] = []
    for path in paths:
        try:
            items.append(_parse_item(path))
        except ValueError as error:
            errors.append(str(error))
    statuses = {item.item_id: item.status for item in items}
    dependencies = {item.item_id: item.blockers for item in items}
    errors.extend(
        f"{item.item_id} has unsupported status {item.status!r}"
        for item in items
        if item.status not in ALLOWED_STATUSES
    )
    seen_ids: set[str] = set()
    for item in items:
        if item.item_id in seen_ids:
            errors.append(f"duplicate work item ID {item.item_id}")
        seen_ids.add(item.item_id)
    errors.extend(_dependency_cycle_errors(dependencies))
    errors.extend(_mirror_errors(spec, items))
    errors.extend(_reference_errors(items))
    link_paths = [spec / "WORK_ITEMS.md", *(item.path for item in items)]
    errors.extend(_local_link_errors(path for path in link_paths if path.exists()))
    frontier = sorted(
        item.item_id
        for item in items
        if item.item_id.startswith("VIG-")
        and item.status in {"Ready for implementation", "In progress"}
        and all(statuses.get(blocker) == "Done" for blocker in item.blockers)
    )
    return ValidationReport(errors=errors, frontier=frontier, item_count=len(items))


def _reference_errors(items: list[WorkItem]) -> list[str]:
    """Check that declared blocker and parent IDs exist."""
    known_ids = {item.item_id for item in items}
    errors: list[str] = []
    for item in items:
        for blocker in item.blockers:
            if blocker not in known_ids:
                errors.append(f"{item.item_id} references unknown blocker {blocker}")
        if item.parent_id is not None and item.parent_id not in known_ids:
            errors.append(f"{item.item_id} references unknown parent {item.parent_id}")
    return errors


def _local_link_errors(paths: Iterable[Path]) -> list[str]:
    """Check all relative Markdown links in backlog files."""
    errors: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_PATTERN.finditer(text):
            target = match.group(1).strip().strip("<>")
            parsed = urlparse(target)
            if parsed.scheme or target.startswith("#"):
                continue
            local_part = unquote(target.split("#", 1)[0])
            if not local_part:
                continue
            resolved = (path.parent / local_part).resolve()
            if not resolved.exists():
                errors.append(f"{path}: broken local link {target!r}")
    return errors


def _dependency_cycle_errors(dependencies: dict[str, tuple[str, ...]]) -> list[str]:
    """Find cycles in blocker edges and describe each cycle once."""
    state: dict[str, int] = {}
    stack: list[str] = []
    errors: list[str] = []
    seen_cycles: set[frozenset[str]] = set()

    def visit(item_id: str) -> None:
        state[item_id] = 1
        stack.append(item_id)
        for blocker in dependencies.get(item_id, ()):
            if blocker not in dependencies:
                continue
            if state.get(blocker, 0) == 0:
                visit(blocker)
            elif state.get(blocker) == 1:
                start = stack.index(blocker)
                cycle = stack[start:] + [blocker]
                key = frozenset(cycle)
                if key not in seen_cycles:
                    seen_cycles.add(key)
                    errors.append("dependency cycle: " + " -> ".join(cycle))
        stack.pop()
        state[item_id] = 2

    for item_id in sorted(dependencies):
        if state.get(item_id, 0) == 0:
            visit(item_id)
    return errors


def _mirror_errors(spec: Path, items: list[WorkItem]) -> list[str]:
    """Check child status mirrors and epic progress counters."""
    errors: list[str] = []
    by_id = {item.item_id: item for item in items}
    registry_path = spec / "WORK_ITEMS.md"
    registry_text = registry_path.read_text(encoding="utf-8") if registry_path.exists() else ""
    registry = {
        match.group(1): (match.group(3), int(match.group(4)), int(match.group(5)))
        for match in REGISTRY_PATTERN.finditer(registry_text)
    }

    for epic in (item for item in items if item.item_id.startswith("EPIC-")):
        text = epic.path.read_text(encoding="utf-8")
        checklist = list(CHECKLIST_PATTERN.finditer(text))
        checklist_ids = [match.group(2) for match in checklist]
        positions = {child_id: index for index, child_id in enumerate(checklist_ids)}
        children: list[WorkItem] = []
        for match in checklist:
            checked = match.group(1).lower() == "x"
            child_id = match.group(2)
            mirror_status = match.group(4)
            child = by_id.get(child_id)
            if child is None:
                errors.append(f"{epic.item_id} checklist references unknown {child_id}")
                continue
            children.append(child)
            if child.status != mirror_status:
                errors.append(
                    f"{child_id} checklist status {mirror_status!r}, issue status {child.status!r}"
                )
            expected_checked = child.status == "Done"
            if checked != expected_checked:
                marker = "checked" if checked else "unchecked"
                errors.append(f"{child_id} checklist is {marker}, issue status is {child.status!r}")
            if child.parent_id != epic.item_id:
                errors.append(
                    f"{child_id} parent is {child.parent_id or 'missing'}, expected {epic.item_id}"
                )

        expected_children = [item for item in items if item.parent_id == epic.item_id]
        for child in expected_children:
            count = checklist_ids.count(child.item_id)
            if count == 0:
                errors.append(f"{child.item_id} is missing from {epic.item_id} checklist")
            elif count > 1:
                errors.append(
                    f"{child.item_id} appears {count} times in {epic.item_id} checklist"
                )
            child_position = positions.get(child.item_id)
            if child_position is None:
                continue
            for blocker in child.blockers:
                blocker_position = positions.get(blocker)
                if blocker_position is not None and child_position < blocker_position:
                    errors.append(
                        f"{child.item_id} appears before blocker {blocker} "
                        f"in {epic.item_id} checklist"
                    )

        entry = registry.get(epic.item_id)
        if entry is None:
            errors.append(f"{epic.item_id} is missing from spec/WORK_ITEMS.md registry")
            continue
        registry_status, registry_done, registry_total = entry
        if registry_status != epic.status:
            errors.append(
                f"{epic.item_id} registry status {registry_status!r}, epic status {epic.status!r}"
            )
        expected_done = sum(child.status == "Done" for child in children)
        expected_total = len(checklist)
        if (registry_done, registry_total) != (expected_done, expected_total):
            errors.append(
                f"{epic.item_id} registry progress {registry_done}/{registry_total}, "
                f"expected {expected_done}/{expected_total}"
            )
    return errors


def _parse_item(path: Path) -> WorkItem:
    text = path.read_text(encoding="utf-8")
    explicit_id = EXPLICIT_ID_PATTERN.search(text)
    heading = re.search(r"^# .+$", text, re.MULTILINE)
    heading_id = ID_PATTERN.search(heading.group(0)) if heading else None
    if explicit_id is None and heading_id is None:
        raise ValueError(f"{path}: missing work item ID in ID metadata or H1")
    item_id = explicit_id.group(1) if explicit_id else heading_id.group(0)
    status_match = STATUS_PATTERN.search(text)
    if status_match is None:
        raise ValueError(f"{path}: missing Status metadata")
    status = status_match.group(1).strip().strip("`")
    dependency = DEPENDENCY_PATTERN.search(text)
    blockers = tuple(ID_PATTERN.findall(dependency.group(1))) if dependency else ()
    parent = PARENT_PATTERN.search(text)
    parent_ids = ID_PATTERN.findall(parent.group(1)) if parent else []
    parent_id = parent_ids[0] if parent_ids else None
    return WorkItem(
        item_id=item_id,
        status=status,
        blockers=blockers,
        parent_id=parent_id,
        path=path,
    )


def main() -> int:
    """Run the validator CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path)
    args = parser.parse_args()
    report = validate_repository(args.root)
    if report.errors:
        for error in report.errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {report.item_count} work items")
    print("Frontier: " + (", ".join(report.frontier) if report.frontier else "empty"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
