#!/usr/bin/env python3
"""Behavior tests for skill_inventory.py."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("skill_inventory.py")
SPEC = importlib.util.spec_from_file_location("skill_inventory", MODULE_PATH)
assert SPEC and SPEC.loader
skill_inventory = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = skill_inventory
SPEC.loader.exec_module(skill_inventory)


def write_skill(root: Path, name: str, body: str = "Do useful work.\n") -> Path:
    """Create a minimal valid skill fixture."""

    directory = root / name
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test skill.\n---\n\n{body}", encoding="utf-8"
    )
    return directory


class InventoryTest(unittest.TestCase):
    """Verify observable audit and linking behavior."""

    def test_classifies_identical_missing_and_different_skills(self) -> None:
        """The audit distinguishes the states needed for a merge proposal."""

        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            codex = base / "codex"
            claude = base / "claude"
            write_skill(codex, "same")
            write_skill(claude, "same")
            write_skill(codex, "left")
            write_skill(claude, "right")
            write_skill(codex, "changed", "Codex behavior.\n")
            write_skill(claude, "changed", "Claude behavior.\n")

            report = skill_inventory.inventory([codex], [claude])
            states = {row["name"]: row["state"] for row in report["skills"]}

            self.assertEqual("identical", states["same"])
            self.assertEqual("codex-only", states["left"])
            self.assertEqual("claude-only", states["right"])
            self.assertEqual("different", states["changed"])

    def test_link_missing_dry_run_does_not_mutate(self) -> None:
        """Planning missing links leaves both roots unchanged."""

        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            codex = base / "codex"
            claude = base / "claude"
            write_skill(codex, "left")
            claude.mkdir()
            report = skill_inventory.inventory([codex], [claude])

            operations, blockers = skill_inventory.link_operations(report, codex, claude)

            self.assertFalse(blockers)
            self.assertEqual(1, len(operations))
            self.assertFalse((claude / "left").exists())

    def test_apply_links_creates_non_overwriting_symlinks(self) -> None:
        """Applying a plan creates a link and refuses a second overwrite."""

        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = write_skill(base / "codex", "left")
            destination = base / "claude" / "left"
            operation = {"source": str(source), "destination": str(destination)}

            skill_inventory.apply_links([operation])

            self.assertTrue(destination.is_symlink())
            self.assertEqual(source.resolve(), destination.resolve())
            with self.assertRaises(RuntimeError):
                skill_inventory.apply_links([operation])

    def test_reports_broken_symlink_without_following_it(self) -> None:
        """A broken entry is diagnostic data, not a crash."""

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "broken").symlink_to(root / "missing", target_is_directory=True)

            entries, diagnostics = skill_inventory.discover_skills("claude", [root])

            self.assertFalse(entries)
            self.assertEqual("broken skill symlink", diagnostics[0].message)


if __name__ == "__main__":
    unittest.main()
