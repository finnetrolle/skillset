# Cavecrew

Portable delegation guidance for Codex and Claude Code: code investigation,
small edits and focused review with compact results.

The package contains its own role instructions. It uses the delegation mechanism
available in the current host; named agent presets and plugin hooks are optional.
When delegation is unavailable, the same contracts can guide inline work.

Start with [SKILL.md](SKILL.md) for routing and task briefs. Role definitions:

- [Investigator](references/investigator.md): locate code, callers and tests.
- [Builder](references/builder.md): edit 1-2 known project files.
- [Reviewer](references/reviewer.md): inspect changes or specified files.
- [Shared contract](references/shared.md): scope, evidence and reporting rules.

Keep the session's model settings unless the user or applicable instructions
choose an available override. No model patching or external preset installation
is performed by this package. Token savings are not assumed or quantified.
