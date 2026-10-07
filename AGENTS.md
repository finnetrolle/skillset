# Skillset

This repository is the source of truth for the user's skills. Edit `skills/`,
then install explicitly; never edit deployed copies as part of repository work.

- Preserve the user's intent and existing invocation policy.
- Keep portable instructions in `SKILL.md`; use relative paths for resources.
- Retain the provenance and license of imported material.
- Never overwrite locally edited deployed skills without an explicit option.
- Test installation, conflict detection and rollback through the public CLI in
  temporary directories. Tests must never use the real home skill directories.
- Use `make check` and `make test` before committing changes to the manager.
- Behavioral evaluation of complex skill changes may use independent subagents
  with isolated fixtures and no external mutations. This is evaluation, not
  permission to apply unrelated changes or publish evaluation artifacts.
- Use the repository's skill manager and local tools to maintain this set.
- Do not use GitHub Actions. Keep validation local; do not add workflows or
  dispatch remote runs.
- Do not manually edit generated files or CHANGELOG.md.
