"""Behavioral tests through the CLI; every home and deployment path is temporary."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/manage.py"


class ManagerCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repository"
        self.target = self.root / "deployed"
        self.home = self.root / "home"
        self.home.mkdir()
        self.lock = {"schema_version": 1, "skills": {}, "upstreams": {}}
        for name in ("alpha", "beta"):
            directory = self.repo / "skills" / name
            directory.mkdir(parents=True)
            text = f"---\nname: {name}\ndescription: Handle {name} requests.\n---\n\nInitial {name} instruction.\n"
            (directory / "SKILL.md").write_text(text)
            (directory / "fixture.txt").write_text("retained resource\n")
            (directory / "run.sh").write_text("#!/bin/sh\nprintf 'fixture\\n'\n")
            (directory / "run.sh").chmod(0o755)
            baseline = {p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "executable": p.name == "run.sh"} for p in directory.iterdir()}
            self.lock["skills"][name] = {"origin": "local", "baseline_files": baseline, "dependencies": ["beta"] if name == "alpha" else []}
        self.save_lock()

    def save_lock(self):
        (self.repo / "sources.lock.json").write_text(json.dumps(self.lock))

    def cli(self, *args, code=0):
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.repo), "--json", *args],
                                capture_output=True, text=True, env={**os.environ, "HOME": str(self.home)}, timeout=20)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertFalse(result.stderr, result.stderr)
        return json.loads(result.stdout)

    def deploy(self, *extra, code=0):
        return self.cli("install", "--target", str(self.target), "--skill", "alpha", *extra, code=code)

    def restore(self, *extra, code=0):
        return self.cli("rollback", "--target", str(self.target), *extra, code=code)

    def test_first_install_includes_dependencies_resources_and_modes(self):
        self.target.mkdir()
        foreign = self.target / "unrelated"
        foreign.mkdir()
        (foreign / "keep.txt").write_text("owned elsewhere")
        result = self.deploy()
        self.assertEqual(result["status"], "installed")
        for name in ("alpha", "beta"):
            for filename in ("SKILL.md", "fixture.txt", "run.sh"):
                self.assertEqual((self.target / name / filename).read_bytes(), (self.repo / "skills" / name / filename).read_bytes())
            self.assertTrue((self.target / name / "run.sh").stat().st_mode & 0o100)
        self.assertEqual((foreign / "keep.txt").read_text(), "owned elsewhere")

    def test_second_install_is_an_idempotent_noop(self):
        self.deploy()
        before = (self.target / ".skillset/state.json").read_bytes()
        result = self.deploy()
        self.assertEqual(result["status"], "unchanged")
        self.assertEqual((self.target / ".skillset/state.json").read_bytes(), before)
        self.assertEqual(len(list((self.target / ".skillset/transactions").iterdir())), 1)

    def test_explicit_rollback_overwrite_retains_later_manual_edits(self):
        self.deploy()
        text = "Manual work after deployment.\n"
        (self.target / "alpha/fixture.txt").write_text(text)
        self.restore(code=1)
        result = self.restore("--overwrite-edits")
        backups = Path(result["edit_backups"])
        paths = json.loads((backups / "paths.json").read_text())
        slot = next(key for key, path in paths.items() if Path(path).resolve() == (self.target / "alpha").resolve())
        self.assertEqual((backups / slot / "fixture.txt").read_text(), text)
        self.assertFalse((self.target / "alpha").exists())

    def test_upstream_check_and_diff_preserve_local_adaptations_and_pin(self):
        upstream = self.root / "upstream"
        upstream.mkdir()
        def git(*args):
            result = subprocess.run(["git", "-C", str(upstream), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", *args], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout.strip()
        git("init", "-b", "main")
        package = upstream / "skills/alpha"
        package.mkdir(parents=True)
        (package / "SKILL.md").write_text("Original upstream instruction.\n")
        git("add", ".")
        git("commit", "-m", "Initial")
        pinned = git("rev-parse", "HEAD")
        (package / "SKILL.md").write_text("New upstream instruction.\n")
        (package / "resource.txt").write_text("New upstream resource.\n")
        git("add", ".")
        git("commit", "-m", "Update")
        latest = git("rev-parse", "HEAD")
        self.lock["upstreams"]["fixture"] = {"repository": str(upstream), "revision": pinned, "skill_paths": {"alpha": "skills/alpha"}}
        self.save_lock()
        original_lock = (self.repo / "sources.lock.json").read_bytes()
        original_skill = (self.repo / "skills/alpha/SKILL.md").read_bytes()
        self.assertEqual(self.cli("upstream-check")["sources"][0]["status"], "update-available")
        output = self.root / "patch.diff"
        result = self.cli("upstream-diff", "--source", "fixture", "--skill", "alpha", "--full", "--output", str(output))
        self.assertEqual(result["pinned"], pinned)
        self.assertEqual(result["latest"], latest)
        self.assertIn("resource.txt", output.read_text())
        self.assertIn("Initial alpha instruction.", result["local_instruction_patch"])
        self.assertEqual((self.repo / "sources.lock.json").read_bytes(), original_lock)
        self.assertEqual((self.repo / "skills/alpha/SKILL.md").read_bytes(), original_skill)

    def test_update_and_rollback_restore_the_previous_contents_and_manifest(self):
        self.deploy()
        before = (self.target / "alpha/SKILL.md").read_text()
        state = (self.target / ".skillset/state.json").read_bytes()
        (self.repo / "skills/alpha/SKILL.md").write_text(before + "New instruction.\n")
        self.deploy()
        self.assertIn("New instruction", (self.target / "alpha/SKILL.md").read_text())
        self.assertEqual(self.restore()["status"], "rolled-back")
        self.assertEqual((self.target / "alpha/SKILL.md").read_text(), before)
        self.assertEqual((self.target / ".skillset/state.json").read_bytes(), state)

    def test_unmanaged_manual_edits_abort_the_entire_install(self):
        shutil.copytree(self.repo / "skills/alpha", self.target / "alpha")
        text = "---\nname: alpha\ndescription: Custom.\n---\nHuman edits.\n"
        (self.target / "alpha/SKILL.md").write_text(text)
        result = self.deploy(code=1)
        self.assertIn("Local edits", result["error"])
        self.assertEqual((self.target / "alpha/SKILL.md").read_text(), text)
        self.assertFalse((self.target / "beta").exists())
        self.assertFalse((self.target / ".skillset").exists())

    def test_imported_baseline_can_be_updated_and_restored(self):
        shutil.copytree(self.repo / "skills/alpha", self.target / "alpha")
        before = (self.target / "alpha/SKILL.md").read_text()
        (self.repo / "skills/alpha/SKILL.md").write_text(before + "Portable changes.\n")
        self.deploy()
        self.restore()
        self.assertEqual((self.target / "alpha/SKILL.md").read_text(), before)
        self.assertFalse((self.target / "beta").exists())

    def test_tracked_manual_edits_require_an_explicit_option_and_are_backed_up(self):
        self.deploy()
        path = self.target / "alpha/SKILL.md"
        manual = path.read_text() + "Manual edit.\n"
        path.write_text(manual)
        self.deploy(code=1)
        self.assertEqual(path.read_text(), manual)
        self.deploy("--overwrite-edits")
        self.assertNotIn("Manual edit", path.read_text())
        self.restore()
        self.assertEqual(path.read_text(), manual)

    def test_rollback_refuses_to_overwrite_later_manual_edits(self):
        self.deploy()
        source = self.repo / "skills/alpha/SKILL.md"
        source.write_text(source.read_text() + "Repository update.\n")
        self.deploy()
        path = self.target / "alpha/SKILL.md"
        text = path.read_text() + "Later manual edit.\n"
        path.write_text(text)
        result = self.restore(code=1)
        self.assertIn("Local edits", result["error"])
        self.assertEqual(path.read_text(), text)

    def test_dry_run_does_not_create_the_target(self):
        result = self.deploy("--dry-run")
        self.assertEqual(result["status"], "dry-run")
        self.assertFalse(self.target.exists())

    def test_legacy_migration_and_rollback_preserve_unrelated_skills(self):
        legacy = self.root / "legacy"
        shutil.copytree(self.repo / "skills/alpha", legacy / "alpha")
        (legacy / "system").mkdir()
        (legacy / "system/keep").write_text("foreign")
        self.deploy("--migrate-from", str(legacy))
        self.assertFalse((legacy / "alpha").exists())
        self.assertTrue((self.target / "alpha/SKILL.md").is_file())
        self.restore()
        self.assertTrue((legacy / "alpha/SKILL.md").is_file())
        self.assertFalse((self.target / "alpha").exists())
        self.assertEqual((legacy / "system/keep").read_text(), "foreign")

    def test_legacy_conflict_is_detected_before_installation(self):
        legacy = self.root / "legacy"
        shutil.copytree(self.repo / "skills/alpha", legacy / "alpha")
        path = legacy / "alpha/fixture.txt"
        path.write_text("human edits")
        self.deploy("--migrate-from", str(legacy), code=1)
        self.assertFalse(self.target.exists())
        self.assertEqual(path.read_text(), "human edits")

    def test_unknown_flags_and_skill_names_have_structured_usage_errors(self):
        result = self.cli("install", "--targte", str(self.target), code=2)
        self.assertIn("unrecognized arguments", result["error"])
        self.assertIn("--target", result["help"])
        self.cli("install", "--skill", "../escape", "--target", str(self.target), code=2)
        self.assertFalse(self.target.exists())

    def test_resource_escape_and_missing_references_block_installation(self):
        path = self.repo / "skills/alpha/SKILL.md"
        original = path.read_text()
        path.write_text(original + "Read [missing](references/missing.md).\n")
        self.deploy(code=1)
        self.assertFalse(self.target.exists())
        path.write_text(original)
        (self.repo / "skills/alpha/outside").symlink_to(self.root / "home", target_is_directory=True)
        self.deploy(code=1)
        self.assertFalse(self.target.exists())

    def test_corrupted_backup_cannot_replace_current_contents(self):
        first = self.deploy()
        (self.repo / "skills/alpha/fixture.txt").write_text("updated fixture")
        update = self.deploy()
        directory = self.target / ".skillset/transactions" / update["transaction"]
        record = json.loads((directory / "transaction.json").read_text())
        index = next(i for i, op in enumerate(record["operations"]) if op["name"] == "alpha")
        (directory / str(index) / "before/fixture.txt").write_text("corrupted backup")
        self.restore(code=1)
        self.assertEqual((self.target / "alpha/fixture.txt").read_text(), "updated fixture")

    def test_target_inside_repository_is_rejected(self):
        self.cli("install", "--target", str(self.repo / "skills"), code=2)
        self.assertFalse((self.repo / "skills/.skillset").exists())

    def test_duplicate_yaml_metadata_is_rejected(self):
        path = self.repo / "skills/alpha/SKILL.md"
        path.write_text(path.read_text().replace("name: alpha", "name: alpha\nname: alpha"))
        result = self.cli("check", code=1)
        self.assertIn("Duplicate YAML key", "; ".join(result["errors"]))

    def test_no_arguments_show_a_complete_catalog(self):
        result = self.cli()
        self.assertEqual(result["total"], 2)
        self.assertEqual({row["name"] for row in result["skills"]}, {"alpha", "beta"})

    def crash(self, stage):
        driver = self.root / "fault.py"
        driver.write_text(f'''import importlib.util, os, sys
spec = importlib.util.spec_from_file_location("manager", {str(SCRIPT)!r})
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)
original = manager.atomic_json
def interrupted(path, data):
    if path.name == "state.json":
        os._exit(77)
    return original(path, data)
manager.atomic_json = interrupted
raise SystemExit(manager.main(sys.argv[1:]))
''')
        result = subprocess.run([sys.executable, str(driver), "--repo", str(self.repo), "--json", stage,
                                 "--target", str(self.target)], capture_output=True, text=True,
                                env={**os.environ, "HOME": str(self.home)}, timeout=20)
        self.assertEqual(result.returncode, 77, result.stdout + result.stderr)

    def test_interrupted_install_can_be_recovered_without_overwriting_manual_edits(self):
        shutil.copytree(self.repo / "skills/alpha", self.target / "alpha")
        before = (self.target / "alpha/SKILL.md").read_text()
        (self.repo / "skills/alpha/SKILL.md").write_text(before + "Updated source.\n")
        self.crash("install")
        self.assertIn("Updated source", (self.target / "alpha/SKILL.md").read_text())
        self.assertEqual(self.restore()["status"], "rolled-back")
        self.assertEqual((self.target / "alpha/SKILL.md").read_text(), before)
        self.assertFalse((self.target / "beta").exists())

    def test_interrupted_rollback_is_resumable(self):
        self.deploy()
        before = (self.target / "alpha/SKILL.md").read_text()
        (self.repo / "skills/alpha/SKILL.md").write_text(before + "Updated source.\n")
        self.deploy()
        self.crash("rollback")
        self.assertEqual(self.restore()["status"], "rolled-back")
        self.assertEqual((self.target / "alpha/SKILL.md").read_text(), before)

    def test_alias_is_rejected_and_its_referent_is_untouched(self):
        referent = self.root / "other-owner"
        shutil.copytree(self.repo / "skills/alpha", referent)
        self.target.mkdir()
        (self.target / "alpha").symlink_to(referent, target_is_directory=True)
        self.deploy(code=1)
        self.assertTrue((self.target / "alpha").is_symlink())
        self.assertEqual((referent / "fixture.txt").read_text(), "retained resource\n")


if __name__ == "__main__":
    unittest.main()
