---
name: sync-agent-skills
description: Compare user-authored skill sets available to Codex and Claude Code, identify missing or divergent skills, and propose or apply a safe merge. Use when auditing, aligning, merging, or synchronizing personal or project skills across the two applications. Exclude bundled, managed, synced-account, and plugin-provided skills unless the user explicitly includes them.
---

# Sync Agent Skills

Align the user-managed skill names and content that both applications can load. Do not promise parity for built-in, managed, account-synced, or plugin skills because each host supplies those independently.

## Default scope

Audit personal filesystem skills unless the user specifies a project or custom roots:

- Codex: `~/.agents/skills` and the legacy `${CODEX_HOME:-~/.codex}/skills` location.
- Claude Code: `~/.claude/skills`.
- Exclude hidden directories, Codex `.system`, and Claude Code's reserved `synced` directory.

For project scope, pass the relevant `.agents/skills` and `.claude/skills` directories explicitly. Keep personal and project reports separate because their precedence rules differ.

## Audit first

Resolve this skill directory from the loaded `SKILL.md`, then run:

```bash
python3 <skill-dir>/scripts/skill_inventory.py audit
```

Use repeatable `--codex-root PATH` and `--claude-root PATH` options when the defaults are not the requested scope. The audit compares normalized directory names and deterministic content hashes, follows top-level skill symlinks, and reports invalid entries and portability markers.

Summarize the result in the user's language with these groups:

- present and identical;
- only in Codex;
- only in Claude Code;
- same name but different content;
- ambiguous duplicates within one host;
- invalid or host-specific entries.

Always name the roots included and exclusions applied. A matching name is set parity; a matching hash is content parity.

## Propose the merge

Prefer one portable source of truth in `~/.agents/skills`, with Claude Code entries symlinked from `~/.claude/skills`. Existing skills may remain elsewhere and be linked into the missing host when moving them would add risk.

For skills missing from one host, preview non-overwriting links:

```bash
python3 <skill-dir>/scripts/skill_inventory.py link-missing
```

For every content conflict, inspect the complete directory diff and propose one of:

1. Choose one version when the other is stale.
2. Merge complementary instructions and resources into a portable canonical version.
3. Keep host adapters only when the workflow genuinely depends on host-specific capabilities, and disclose that content parity is intentionally impossible.

Read [references/compatibility.md](references/compatibility.md) before proposing or implementing a content merge. Show the source, destination, conflicts, compatibility concerns, and expected final state. Do not mutate files during the proposal.

## Apply only after approval

Treat approval of the proposal as authorization only for the exact listed operations.

- Create missing links with `link-missing --apply`; the script never overwrites an existing path.
- For content conflicts, stage the merged skill in a temporary directory, validate it, and show the resulting diff before replacing either version.
- Back up every replaced skill directory under `~/.agent-skill-backups/<timestamp>/` while preserving its source label and skill name.
- Never delete built-in, managed, synced-account, or plugin content.
- Never resolve a conflict by timestamp alone or silently choose a winner.
- Do not copy secrets, credentials, caches, generated output, or absolute machine-specific paths into a shared skill.

After changes, rerun `audit`. Report remaining differences and whether they are errors or explicit host-specific exceptions. Mention that a host restart may be needed if its top-level skill directory did not exist when the session started.

## Validation

For a merged skill, verify at least:

- `SKILL.md` exists and its `name` matches the directory name;
- frontmatter has a focused `description`;
- all relative references and scripts exist;
- scripts run with the dependencies available to both hosts;
- host-specific syntax is removed or deliberately isolated;
- the final audit has no unapproved missing skills or conflicts.
