import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

from validate_work_items import validate_repository


class ValidateWorkItemsTest(unittest.TestCase):
    def test_accepts_consistent_backlog_and_reports_frontier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_backlog(root)

            report = validate_repository(root)

            self.assertEqual([], report.errors)
            self.assertEqual(["VIG-01-02"], report.frontier)
            self.assertEqual(3, report.item_count)

    def test_rejects_dependency_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_backlog(root)
            (root / "spec/issues/epic_01/issue_01_01.md").write_text(
                """# VIG-01-01: First

**Статус:** Ready for implementation
**Epic:** [EPIC-01](../../epics/epic_01_example.md)
**Зависит от:** [VIG-01-02](issue_01_02.md)
""",
                encoding="utf-8",
            )

            report = validate_repository(root)

            self.assertTrue(
                any("dependency cycle" in error for error in report.errors),
                report.errors,
            )

    def test_rejects_checklist_status_and_registry_progress_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_backlog(root)
            epic = root / "spec/epics/epic_01_example.md"
            epic.write_text(
                epic.read_text(encoding="utf-8").replace(
                    "VIG-01-02: Second](../issues/epic_01/issue_01_02.md) - `Ready for implementation`",
                    "VIG-01-02: Second](../issues/epic_01/issue_01_02.md) - `Draft`",
                ),
                encoding="utf-8",
            )
            registry = root / "spec/WORK_ITEMS.md"
            registry.write_text(
                registry.read_text(encoding="utf-8").replace("1/2", "2/2"),
                encoding="utf-8",
            )

            report = validate_repository(root)

            self.assertTrue(
                any("VIG-01-02 checklist status" in error for error in report.errors),
                report.errors,
            )
            self.assertTrue(
                any("EPIC-01 registry progress 2/2, expected 1/2" in error for error in report.errors),
                report.errors,
            )

    def test_rejects_broken_local_link_and_unknown_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_backlog(root)
            issue = root / "spec/issues/epic_01/issue_01_02.md"
            issue.write_text(
                issue.read_text(encoding="utf-8")
                .replace("../../epics/epic_01_example.md", "../../epics/missing.md")
                .replace("VIG-01-01](issue_01_01.md)", "VIG-99-99](missing.md)"),
                encoding="utf-8",
            )

            report = validate_repository(root)

            self.assertTrue(
                any("broken local link" in error for error in report.errors),
                report.errors,
            )
            self.assertTrue(
                any("unknown blocker VIG-99-99" in error for error in report.errors),
                report.errors,
            )

    def test_rejects_unknown_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_backlog(root)
            issue = root / "spec/issues/epic_01/issue_01_02.md"
            issue.write_text(
                issue.read_text(encoding="utf-8").replace(
                    "Ready for implementation", "Review"
                ),
                encoding="utf-8",
            )
            epic = root / "spec/epics/epic_01_example.md"
            epic.write_text(
                epic.read_text(encoding="utf-8").replace(
                    "VIG-01-02: Second](../issues/epic_01/issue_01_02.md) - `Ready for implementation`",
                    "VIG-01-02: Second](../issues/epic_01/issue_01_02.md) - `Review`",
                ),
                encoding="utf-8",
            )

            report = validate_repository(root)

            self.assertIn("VIG-01-02 has unsupported status 'Review'", report.errors)

    def test_rejects_child_missing_from_epic_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_backlog(root)
            epic = root / "spec/epics/epic_01_example.md"
            lines = epic.read_text(encoding="utf-8").splitlines()
            epic.write_text(
                "\n".join(line for line in lines if "VIG-01-02" not in line) + "\n",
                encoding="utf-8",
            )
            registry = root / "spec/WORK_ITEMS.md"
            registry.write_text(
                registry.read_text(encoding="utf-8").replace("1/2", "1/1"),
                encoding="utf-8",
            )

            report = validate_repository(root)

            self.assertIn("VIG-01-02 is missing from EPIC-01 checklist", report.errors)

    def test_rejects_checklist_before_its_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_backlog(root)
            epic = root / "spec/epics/epic_01_example.md"
            text = epic.read_text(encoding="utf-8")
            first = "- [x] [VIG-01-01: First](../issues/epic_01/issue_01_01.md) - `Done`"
            second = "- [ ] [VIG-01-02: Second](../issues/epic_01/issue_01_02.md) - `Ready for implementation`"
            epic.write_text(text.replace(f"{first}\n{second}", f"{second}\n{first}"), encoding="utf-8")

            report = validate_repository(root)

            self.assertIn(
                "VIG-01-02 appears before blocker VIG-01-01 in EPIC-01 checklist",
                report.errors,
            )

    def test_reports_malformed_item_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_backlog(root)
            issue = root / "spec/issues/epic_01/issue_01_02.md"
            issue.write_text(
                issue.read_text(encoding="utf-8").replace(
                    "**Статус:** Ready for implementation\n", ""
                ),
                encoding="utf-8",
            )

            report = validate_repository(root)

            self.assertTrue(
                any("missing Status metadata" in error for error in report.errors),
                report.errors,
            )

    @staticmethod
    def write_valid_backlog(root: Path) -> None:
        epic = root / "spec/epics/epic_01_example.md"
        first = root / "spec/issues/epic_01/issue_01_01.md"
        second = root / "spec/issues/epic_01/issue_01_02.md"
        epic.parent.mkdir(parents=True)
        first.parent.mkdir(parents=True)

        (root / "spec/WORK_ITEMS.md").write_text(
            """# Work items

| Work item | Status | Progress |
|---|---|---:|
| [EPIC-01: Example](epics/epic_01_example.md) | `In progress` | 1/2 |
""",
            encoding="utf-8",
        )
        epic.write_text(
            """# Example epic

**ID:** `EPIC-01`
**Статус:** In progress

## Child issues

- [x] [VIG-01-01: First](../issues/epic_01/issue_01_01.md) - `Done`
- [ ] [VIG-01-02: Second](../issues/epic_01/issue_01_02.md) - `Ready for implementation`
""",
            encoding="utf-8",
        )
        first.write_text(
            """# VIG-01-01: First

**Статус:** Done
**Epic:** [EPIC-01](../../epics/epic_01_example.md)
**Зависит от:** нет
""",
            encoding="utf-8",
        )
        second.write_text(
            """# VIG-01-02: Second

**Статус:** Ready for implementation
**Epic:** [EPIC-01](../../epics/epic_01_example.md)
**Зависит от:** [VIG-01-01](issue_01_01.md)
""",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
