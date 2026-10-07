#!/usr/bin/env python3
"""Check, deploy and restore versioned skill packages without running their code."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit
import uuid

try:
    import yaml
except ModuleNotFoundError:
    message = {"error": "PyYAML is missing", "help": "Run make setup, then use .venv/bin/python scripts/manage.py."}
    print(json.dumps(message) if "--json" in sys.argv else 'error: "PyYAML is missing"\nhelp: "Run make setup, then use .venv/bin/python scripts/manage.py."')
    raise SystemExit(2)

REPO = Path(__file__).resolve().parent.parent
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IGNORED = {".DS_Store", "__pycache__", ".git", "node_modules", ".venv", ".pytest_cache"}


class Failure(Exception):
    def __init__(self, message, help_text="", code=1):
        super().__init__(message)
        self.help = help_text
        self.code = code


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    values = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in values:
            raise Failure(f"Duplicate YAML key: {key}")
        values[key] = loader.construct_object(value_node, deep=deep)
    return values


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read_json(path, default=None):
    if not path.exists() and default is not None:
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Failure(f"Cannot read {path}: {error}") from error


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def within(path, root):
    return path == root or root in path.parents


def valid_name(value):
    if not isinstance(value, str) or not NAME.fullmatch(value) or len(value) > 64:
        raise Failure(f"Invalid skill name: {value!r}", "Use a lowercase hyphenated directory name.")
    return value


def manifest(directory):
    if not directory.is_dir():
        raise Failure(f"Skill directory is missing: {directory}")
    base = directory.resolve()
    result = {}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if any(part in IGNORED for part in relative.parts) or path.suffix in (".pyc", ".pyo"):
            continue
        if path.is_symlink():
            if not within(path.resolve(), base):
                raise Failure(f"Skill symlink escapes its package: {relative}")
            result[relative.as_posix()] = {"symlink": os.readlink(path)}
        elif path.is_file():
            result[relative.as_posix()] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "executable": bool(path.stat().st_mode & stat.S_IXUSR),
            }
    return result


def fingerprint(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def metadata(directory):
    path = directory / "SKILL.md"
    try:
        text = path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if not text.startswith("---\n") or len(parts) != 3:
            raise Failure(f"Missing YAML frontmatter: {path}")
        data = yaml.load(parts[1], Loader=UniqueLoader)
        if not isinstance(data, dict):
            raise Failure(f"Frontmatter is not a mapping: {path}")
        if valid_name(data.get("name")) != directory.name:
            raise Failure(f"Skill name does not match its folder: {path}")
        if not isinstance(data.get("description"), str) or not data["description"].strip():
            raise Failure(f"Missing description: {path}")
        return data, parts[2]
    except (OSError, yaml.YAMLError) as error:
        raise Failure(f"Invalid skill metadata in {path}: {error}") from error


def load_catalog(repo):
    lock = read_json(repo / "sources.lock.json")
    if lock.get("schema_version") != 1 or not isinstance(lock.get("skills"), dict):
        raise Failure("Unsupported sources.lock.json schema")
    for name, record in lock["skills"].items():
        valid_name(name)
        if not isinstance(record, dict):
            raise Failure(f"Invalid catalog entry: {name}")
        for dependency in record.get("dependencies", []):
            valid_name(dependency)
            if dependency not in lock["skills"]:
                raise Failure(f"Missing dependency: {name} requires {dependency}")
    return lock


def select(lock, names):
    selected = set(names or lock["skills"])
    missing = selected - lock["skills"].keys()
    if missing:
        raise Failure("Unknown skills: " + ", ".join(sorted(missing)), "Run python scripts/manage.py list.", 2)
    pending = list(selected)
    while pending:
        for dependency in lock["skills"][pending.pop()].get("dependencies", []):
            if dependency not in selected:
                selected.add(dependency)
                pending.append(dependency)
    return sorted(selected)


def markdown_links(path):
    # Examples inside fenced code blocks are not live resource references.
    text = re.sub(r"(?ms)^\s*(`{3,}|~{3,}).*?^\s*\1\s*$", "", path.read_text(encoding="utf-8"))
    for value in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
        value = value.strip().split(' "', 1)[0].strip("<>")
        if not value or value.startswith("#") or "$" in value or "{" in value or "<" in value:
            continue
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc:
            continue
        yield unquote(parsed.path)


def check(repo, lock, names=None):
    errors = []
    selected = select(lock, names)
    actual = {p.name for p in (repo / "skills").iterdir() if p.is_dir() and not p.name.startswith(".")}
    if actual != set(lock["skills"]):
        errors.append("Catalog/folder mismatch: " + ", ".join(sorted(actual ^ set(lock["skills"]))))
    files = 0
    for name in selected:
        directory = repo / "skills" / name
        try:
            metadata(directory)
            files += len(manifest(directory))
            # Validate actual entry points and their directly linked reference docs.
            documents = {directory / "SKILL.md"}
            visited = set()
            while documents:
                document = documents.pop()
                if document in visited:
                    continue
                visited.add(document)
                for link in markdown_links(document):
                    reference = (document.parent / link).resolve()
                    if Path(link).is_absolute():
                        errors.append(f"{name}: machine-specific resource link {link}")
                    elif not within(reference, (repo / "skills").resolve()):
                        errors.append(f"{name}: resource link escapes skills/ ({link})")
                    elif not reference.exists():
                        errors.append(f"{name}: missing resource {link} in {document.relative_to(repo)}")
                    elif reference.suffix == ".md" and reference.is_file():
                        documents.add(reference)
            ui = directory / "agents/openai.yaml"
            if ui.exists():
                settings = yaml.load(ui.read_text(encoding="utf-8"), Loader=UniqueLoader) or {}
                interface = settings.get("interface", {})
                for field in ("icon_small", "icon_large"):
                    if field in interface and not (directory / interface[field]).is_file():
                        errors.append(f"{name}: missing {field} resource {interface[field]}")
        except (Failure, OSError, yaml.YAMLError) as error:
            errors.append(str(error))
    return {"status": "ok" if not errors else "failed", "skills": len(selected), "files": files, "errors": errors}


def require_check(repo, lock, names):
    result = check(repo, lock, names)
    if result["errors"]:
        raise Failure("; ".join(result["errors"]), "Run python scripts/manage.py check and fix the reported resources.")


def target_path(value, repo):
    path = Path(value).expanduser().resolve()
    if path in (Path(path.anchor), Path.home().resolve()) or within(path, repo.resolve()) or within(repo.resolve(), path):
        raise Failure(f"Unsafe installation target: {path}", "Use a dedicated skills directory outside this repository.", 2)
    return path


def state_file(target):
    return target / ".skillset" / "state.json"


def load_state(target):
    result = read_json(state_file(target), {"schema_version": 1, "skills": {}, "last_transaction": None})
    if result.get("schema_version") != 1 or not isinstance(result.get("skills"), dict):
        raise Failure("Unsupported installation manifest")
    if result.get("target") and result["target"] != str(target):
        raise Failure("Installation manifest belongs to a different target")
    for name in result["skills"]:
        valid_name(name)
    return result


def present(path):
    return path.exists() or path.is_symlink()


def plan_install(repo, lock, names, target, migrations, overwrite=False):
    state = load_state(target)
    rows = []
    conflicts = []
    for name in names:
        desired = manifest(repo / "skills" / name)
        destination = target / name
        if destination.is_symlink():
            raise Failure(f"Deployment entry is a symlink: {destination}", "Use the canonical skills directory; this command never replaces an alias or edits its referent.")
        observed = manifest(destination) if present(destination) else None
        tracked = state["skills"].get(name)
        baseline = lock["skills"][name].get("baseline_files")
        if observed == desired:
            action = "unchanged" if tracked and tracked["files"] == desired else "adopt"
        elif observed is None:
            action = "install"
        elif (tracked and tracked["files"] == observed) or (not tracked and observed == baseline) or overwrite:
            action = "update"
        else:
            action = "conflict"
            conflicts.append(str(destination))
        rows.append({"name": name, "action": action, "observed": observed, "desired": desired})
        for legacy in migrations:
            old = legacy / name
            if not present(old):
                continue
            if old.is_symlink():
                raise Failure(f"Migration entry is a symlink: {old}", "Retire aliases separately after reviewing their owners and targets.")
            legacy_files = manifest(old)
            if legacy_files not in (desired, baseline) and not overwrite:
                conflicts.append(str(old))
            rows.append({"name": name, "action": "migrate", "legacy": str(old), "observed": legacy_files})
    if conflicts:
        raise Failure("Local edits or unmanaged contents: " + ", ".join(conflicts),
                      "Review with diff. Preserve edits in skills/ or explicitly use --overwrite-edits; backups are retained.")
    return state, rows


def brief_rows(rows):
    return [{"name": row["name"], "action": row["action"]} for row in rows]


def copy_path(source, destination, clean=False):
    if source.is_symlink():
        destination.symlink_to(os.readlink(source), target_is_directory=source.is_dir())
    elif source.is_dir():
        ignore = (lambda folder, names: [n for n in names if n in IGNORED or n.endswith((".pyc", ".pyo"))]) if clean else None
        shutil.copytree(source, destination, symlinks=True, ignore=ignore)
    else:
        shutil.copy2(source, destination)


def remove_path(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


@contextlib.contextmanager
def mutation_lock(target):
    meta = target / ".skillset"
    if meta.is_symlink():
        raise Failure("The installation metadata directory must not be a symlink")
    meta.mkdir(parents=True, exist_ok=True)
    lock = meta / "lock"
    if lock.is_symlink():
        raise Failure("The installation lock must not be a symlink")
    with lock.open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise Failure("Another skillset mutation holds the lock", "Wait for the other command to finish.") from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def revision(repo):
    result = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def migration_paths(values, target, repo):
    paths = []
    for value in values:
        path = target_path(value, repo)
        if within(path, target) or within(target, path):
            raise Failure("Migration and destination directories must be separate", code=2)
        if path in paths:
            continue
        paths.append(path)
    return paths


def install(repo, lock, names, target, migrations, dry_run=False, overwrite=False):
    require_check(repo, lock, names)
    _, rows = plan_install(repo, lock, names, target, migrations, overwrite)
    if dry_run:
        return {"status": "dry-run", "target": str(target), "changes": brief_rows(rows)}
    with mutation_lock(target):
        # Recheck after acquiring the lock so concurrent commands cannot bypass conflicts.
        if (target / ".skillset/pending.json").exists():
            raise Failure("An interrupted transaction requires recovery", f"Run rollback --target {target}.")
        previous, rows = plan_install(repo, lock, names, target, migrations, overwrite)
        changed = [r for r in rows if r["action"] != "unchanged"]
        if not changed:
            return {"status": "unchanged", "skills": len(names), "target": str(target)}
        transaction_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
        transaction = target / ".skillset" / "transactions" / transaction_id
        transaction.mkdir(parents=True)
        operations = []
        for row in rows:
            if row["action"] == "migrate":
                path = Path(row["legacy"])
            elif row["action"] in ("install", "update"):
                path = target / row["name"]
            else:
                continue
            operations.append({"path": str(path), "name": row["name"], "kind": row["action"],
                               "before": row["observed"], "after": None if row["action"] == "migrate" else row["desired"]})
        record = {"id": transaction_id, "target": str(target), "status": "prepared", "previous_state": previous,
                  "allowed_roots": [str(target)] + [str(p) for p in migrations], "operations": operations}
        # Prepare every backup and replacement before touching installed directories.
        for index, operation in enumerate(operations):
            slot = transaction / str(index)
            slot.mkdir()
            path = Path(operation["path"])
            if present(path):
                copy_path(path, slot / "before")
                if manifest(slot / "before") != operation["before"]:
                    raise Failure(f"Installed contents changed while backing up: {path}")
            if operation["after"] is not None:
                copy_path(repo / "skills" / operation["name"], slot / "after", clean=True)
                if manifest(slot / "after") != operation["after"]:
                    raise Failure("Repository changed while staging the installation")
        atomic_json(transaction / "transaction.json", record)
        atomic_json(target / ".skillset" / "pending.json", {"transaction": transaction_id})
        mutated = []
        try:
            for index, operation in enumerate(operations):
                path = Path(operation["path"])
                if (manifest(path) if present(path) else None) != operation["before"]:
                    raise Failure(f"Installed contents changed during staging: {path}")
                mutated.append(index)
                remove_path(path)
                if operation["after"] is not None:
                    (transaction / str(index) / "after").replace(path)
            current = json.loads(json.dumps(previous))
            current["target"] = str(target)
            current["last_transaction"] = transaction_id
            desired_by_name = {row["name"]: row["desired"] for row in rows if row["action"] != "migrate"}
            for name in names:
                desired = desired_by_name[name]
                if manifest(target / name) != desired:
                    raise Failure(f"Installed contents changed before commit: {target / name}")
                current["skills"][name] = {"files": desired, "source_revision": revision(repo), "fingerprint": fingerprint(desired)}
            atomic_json(state_file(target), current)
            record["status"] = "installed"
            atomic_json(transaction / "transaction.json", record)
            (target / ".skillset" / "pending.json").unlink()
        except BaseException:
            # Restore only paths that this transaction actually mutated.
            for index in reversed(mutated):
                operation = operations[index]
                path = Path(operation["path"])
                slot = transaction / str(index)
                remove_path(path)
                if present(slot / "before"):
                    copy_path(slot / "before", path)
            atomic_json(state_file(target), previous)
            record["status"] = "failed-restored"
            atomic_json(transaction / "transaction.json", record)
            (target / ".skillset" / "pending.json").unlink(missing_ok=True)
            raise
        return {"status": "installed", "target": str(target), "transaction": transaction_id, "changes": brief_rows(rows),
                "help": f"Rollback: python scripts/manage.py rollback --target {target}"}


def transaction_record(target, transaction_id):
    if not re.fullmatch(r"\d{8}T\d{6}-[0-9a-f]{8}", transaction_id or ""):
        raise Failure("No valid transaction to roll back", "Run install first or supply --transaction <id>.")
    directory = target / ".skillset" / "transactions" / transaction_id
    record = read_json(directory / "transaction.json")
    if record.get("id") != transaction_id or record.get("target") != str(target):
        raise Failure("Transaction does not belong to this target")
    roots = [Path(p) for p in record["allowed_roots"]]
    for operation in record["operations"]:
        name = valid_name(operation["name"])
        path = Path(operation["path"])
        if not path.is_absolute() or path.name != name or path.parent not in roots:
            raise Failure("Unsafe path in transaction record")
    return directory, record


def rollback(target, transaction_id=None, overwrite=False):
    with mutation_lock(target):
        state = load_state(target)
        pending = read_json(target / ".skillset" / "pending.json", {})
        transaction_id = transaction_id or pending.get("transaction") or state.get("last_transaction")
        directory, record = transaction_record(target, transaction_id)
        if record["status"] == "rolled-back":
            return {"status": "unchanged", "transaction": transaction_id}
        if record["status"] not in ("installed", "prepared", "restoring"):
            raise Failure(f"Transaction cannot be restored from status {record['status']}")
        if record["status"] == "installed" and state.get("last_transaction") != transaction_id:
            raise Failure("Only the latest installed transaction can be rolled back", "Roll back newer transactions first.")
        replaced_edits = []
        for index, operation in enumerate(record["operations"]):
            path = Path(operation["path"])
            observed = manifest(path) if present(path) else None
            accepted = (operation["after"], operation["before"], None) if record["status"] in ("prepared", "restoring") else (operation["after"],)
            if observed not in accepted and not overwrite:
                raise Failure(f"Local edits prevent rollback: {path}", "Preserve the edits or explicitly use --overwrite-edits.")
            if observed not in accepted and observed is not None:
                replaced_edits.append((index, path, observed))
            before = directory / str(index) / "before"
            if operation["before"] is not None and (not present(before) or manifest(before) != operation["before"]):
                raise Failure(f"Backup is missing or changed: {before}")
        edit_backups = None
        if replaced_edits:
            edit_backups = directory / ("rollback-edits-" + uuid.uuid4().hex[:8])
            edit_backups.mkdir()
            for index, path, observed in replaced_edits:
                copy_path(path, edit_backups / str(index))
                if manifest(edit_backups / str(index)) != observed:
                    raise Failure(f"Local edits changed while backing up: {path}")
            atomic_json(edit_backups / "paths.json", {str(i): str(p) for i, p, _ in replaced_edits})
        record["status"] = "restoring"
        atomic_json(directory / "transaction.json", record)
        atomic_json(target / ".skillset" / "pending.json", {"transaction": transaction_id})
        for index, operation in reversed(list(enumerate(record["operations"]))):
            path = Path(operation["path"])
            before = directory / str(index) / "before"
            replacement = path.parent / ("." + path.name + ".restore-" + uuid.uuid4().hex[:8])
            if present(before):
                copy_path(before, replacement)
            remove_path(path)
            if present(replacement):
                replacement.replace(path)
        atomic_json(state_file(target), record["previous_state"])
        record["status"] = "rolled-back"
        atomic_json(directory / "transaction.json", record)
        (target / ".skillset" / "pending.json").unlink(missing_ok=True)
        return {"status": "rolled-back", "transaction": transaction_id, "paths": len(record["operations"]),
                "edit_backups": str(edit_backups) if edit_backups else None}


def diff(repo, lock, names, target, full=False):
    import difflib
    state = load_state(target)
    rows = []
    for name in names:
        source = manifest(repo / "skills" / name)
        path = target / name
        installed = manifest(path) if present(path) else {}
        files = sorted({key for key in source.keys() | installed.keys() if source.get(key) != installed.get(key)})
        tracked = state["skills"].get(name)
        status = "missing" if not present(path) else "same" if not files else "different"
        if tracked and installed != tracked["files"]:
            status = "locally-edited"
        patches = []
        for filename in files:
            left = path / filename
            right = repo / "skills" / name / filename
            try:
                a = left.read_text().splitlines(keepends=True) if left.is_file() else []
                b = right.read_text().splitlines(keepends=True) if right.is_file() else []
            except (UnicodeError, OSError):
                continue
            patches.append("".join(difflib.unified_diff(a, b, fromfile="installed/" + name + "/" + filename, tofile="repository/" + name + "/" + filename)))
        patch = "\n".join(patches)
        row = {"name": name, "status": status, "files": files, "patch": patch if full else patch[:1500]}
        if not full and len(patch) > 1500:
            row["patch_chars"] = len(patch)
            row["help"] = f"diff --skill {name} --target {target} --full"
        rows.append(row)
    return {"target": str(target), "skills": rows}


def git_call(arguments, timeout=45):
    try:
        result = subprocess.run(["git", *arguments], capture_output=True, text=True, timeout=timeout,
                                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Failure("Upstream Git operation failed", "Check Git availability and network access, then retry.") from error
    if result.returncode:
        raise Failure("Upstream Git operation failed", "Check repository access and network connectivity, then retry.")
    return result.stdout


def upstream_check(lock):
    rows = []
    for name, source in lock.get("upstreams", {}).items():
        output = git_call(["ls-remote", source["repository"], "HEAD"])
        latest = output.split()[0] if output.split() else ""
        if not re.fullmatch(r"[0-9a-f]{40}", latest):
            raise Failure(f"Cannot resolve upstream HEAD: {name}")
        rows.append({"source": name, "pinned": source["revision"], "latest": latest,
                     "status": "current" if latest == source["revision"] else "update-available"})
    return {"sources": rows, "help": "Inspect changes with upstream-diff; this command never updates installed skills."}


def upstream_diff(repo, lock, source_name, skill, output=None, full=False):
    import difflib
    sources = lock.get("upstreams", {})
    if source_name not in sources:
        raise Failure(f"Unknown upstream source: {source_name}", code=2)
    source = sources[source_name]
    comparisons = source.get("skill_paths", {})
    if skill not in comparisons:
        raise Failure(f"No upstream mapping for {skill}", "Inspect sources.lock.json for the available skill_paths.", 2)
    latest = git_call(["ls-remote", source["repository"], "HEAD"]).split()[0]
    pinned = source["revision"]
    if not all(re.fullmatch(r"[0-9a-f]{40}", value) for value in (latest, pinned)):
        raise Failure("Invalid upstream revision")
    cache = repo / ".cache/upstreams" / source_name
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        git_call(["init", "--bare", str(cache)])
    git_call(["-C", str(cache), "fetch", "--depth=1", source["repository"], pinned, latest], timeout=60)
    patch = git_call(["-C", str(cache), "diff", pinned, latest, "--", comparisons[skill]])
    original = git_call(["-C", str(cache), "show", pinned + ":" + comparisons[skill] + "/SKILL.md"])
    local = (repo / "skills" / skill / "SKILL.md").read_text()
    local_patch = "".join(difflib.unified_diff(original.splitlines(keepends=True), local.splitlines(keepends=True),
                                             fromfile="upstream-pinned/SKILL.md", tofile="local/SKILL.md"))
    if output:
        Path(output).write_text(patch, encoding="utf-8")
    return {"source": source_name, "skill": skill, "pinned": pinned, "latest": latest,
            "status": "changed" if patch else "unchanged", "patch": (patch if full else patch[:2000]) if not output else None,
            "patch_chars": len(patch), "local_instruction_patch": local_patch if full else local_patch[:2000],
            "local_instruction_patch_chars": len(local_patch), "output": output,
            "help": "Use --full for complete patches or --output <file> for the upstream package patch. Local patch compares SKILL.md only."}


def scalar(value):
    if value is None:
        return "null"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def toon(data, indent=0):
    lines = []
    prefix = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(prefix + key + ":")
            lines.extend(toon(value, indent + 2))
        elif isinstance(value, list):
            if value and all(isinstance(row, dict) and set(row) == set(value[0]) and all(not isinstance(v, (list, dict)) for v in row.values()) for row in value):
                fields = list(value[0])
                lines.append(prefix + key + f"[{len(value)}]" + "{" + ",".join(fields) + "}:")
                lines.extend(prefix + "  " + ",".join(scalar(row[f]) for f in fields) for row in value)
            elif all(not isinstance(v, (list, dict)) for v in value):
                lines.append(prefix + key + f"[{len(value)}]: " + ",".join(scalar(v) for v in value))
            else:
                lines.append(prefix + key + f"[{len(value)}]:")
                for row in value:
                    if isinstance(row, dict):
                        nested = toon(row, indent + 4)
                        lines.append(prefix + "  - " + nested[0].lstrip())
                        lines.extend(nested[1:])
                    else:
                        lines.append(prefix + "  - " + scalar(row))
        else:
            lines.append(prefix + key + ": " + scalar(value))
    return lines


def emit(data, as_json=False):
    print(json.dumps(data, ensure_ascii=False, indent=2) if as_json else "\n".join(toon(data)))


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Failure(message, self.format_help().strip(), 2)


def parser():
    root = Parser(description="Manage versioned personal skills. No command shows the catalog.")
    root.add_argument("--repo", type=Path, default=REPO, help="Repository directory (default: this script's repository)")
    root.add_argument("--json", action="store_true", help="Output JSON instead of TOON")
    commands = root.add_subparsers(dest="command", parser_class=Parser)
    for name in ("list", "show", "check", "diff", "install", "rollback", "upstream-check", "upstream-diff"):
        command = commands.add_parser(name)
        command.add_argument("--repo", type=Path, default=argparse.SUPPRESS)
        command.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
        if name in ("check", "diff", "install"):
            command.add_argument("--skill", action="append", default=[], help="Select a skill and its dependencies; repeatable")
        if name in ("diff", "install", "rollback"):
            command.add_argument("--target", default=str(Path.home() / ".agents/skills"), help="Deployment directory (default: ~/.agents/skills)")
        if name == "diff":
            command.add_argument("--full", action="store_true", help="Include full text patches instead of a 1500-character preview")
        if name in ("install", "rollback"):
            command.add_argument("--overwrite-edits", action="store_true", help="Explicitly replace local edits; original contents are backed up")
        if name == "install":
            command.add_argument("--dry-run", action="store_true", help="Validate and preview without modifying the target")
            command.add_argument("--migrate-from", action="append", default=[], help="Back up and retire matching legacy copies; repeatable")
        if name == "rollback":
            command.add_argument("--transaction", help="Transaction ID (default: latest installation or interrupted transaction)")
        if name == "show":
            command.add_argument("skill")
            command.add_argument("--full", action="store_true", help="Include the full skill instructions")
        if name == "upstream-diff":
            command.add_argument("--source", default="mattpocock")
            command.add_argument("--skill", required=True)
            command.add_argument("--output", help="Save the upstream patch to a file")
            command.add_argument("--full", action="store_true", help="Include complete upstream and local instruction patches")
    return root


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    as_json = "--json" in argv
    try:
        argument_parser = parser()
        args, unknown = argument_parser.parse_known_args(argv)
        if unknown:
            subparsers = next(action for action in argument_parser._actions if isinstance(action, argparse._SubParsersAction))
            help_parser = subparsers.choices.get(args.command, argument_parser)
            raise Failure("unrecognized arguments: " + " ".join(unknown), help_parser.format_help().strip(), 2)
        repo = args.repo.expanduser().resolve()
        lock = load_catalog(repo)
        command = args.command or "list"
        if command == "list":
            data = {"bin": str(Path(__file__).resolve()).replace(str(Path.home()), "~", 1),
                    "description": "Check, install and restore versioned skill packages", "total": len(lock["skills"]),
                    "skills": [{"name": name, "origin": row["origin"]} for name, row in sorted(lock["skills"].items())],
                    "help": ["python scripts/manage.py show <skill>", "python scripts/manage.py install --dry-run"]}
        elif command == "show":
            names = select(lock, [args.skill])
            info, body = metadata(repo / "skills" / args.skill)
            data = {"name": args.skill, "description": info["description"], "dependencies": [n for n in names if n != args.skill],
                    "origin": lock["skills"][args.skill]["origin"]}
            instructions = body.strip()
            data["instructions"] = instructions if args.full else instructions[:1000]
            if not args.full and len(instructions) > 1000:
                data["instruction_chars"] = len(instructions)
                data["help"] = f"python scripts/manage.py show {args.skill} --full"
        elif command == "check":
            data = check(repo, lock, args.skill)
        elif command in ("diff", "install"):
            names = select(lock, args.skill)
            target = target_path(args.target, repo)
            if (target / ".skillset/pending.json").exists():
                raise Failure("An interrupted transaction requires recovery", f"Run rollback --target {target}.")
            if command == "diff":
                data = diff(repo, lock, names, target, args.full)
            else:
                migrations = migration_paths(args.migrate_from, target, repo)
                data = install(repo, lock, names, target, migrations, args.dry_run, args.overwrite_edits)
        elif command == "rollback":
            data = rollback(target_path(args.target, repo), args.transaction, args.overwrite_edits)
        elif command == "upstream-check":
            data = upstream_check(lock)
        else:
            data = upstream_diff(repo, lock, args.source, args.skill, args.output, args.full)
        emit(data, as_json)
        return 1 if data.get("status") == "failed" else 0
    except Failure as error:
        emit({"error": str(error), "help": error.help}, as_json)
        return error.code
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
        emit({"error": str(error), "help": "Check repository files and target permissions; no permission restrictions are bypassed."}, as_json)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
