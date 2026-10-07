# Cross-host skill compatibility

Read this reference only when reviewing or merging divergent skill content.

## Portable core

Prefer a single directory that both hosts can load:

- `SKILL.md` with a lowercase, hyphenated `name` and a precise `description`;
- ordinary Markdown instructions;
- relative links to `scripts/`, `references/`, and `assets/`;
- scripts that depend only on tools present in both execution environments;
- frontmatter from the open Agent Skills format when it is needed.

Codex-specific `agents/openai.yaml` may remain as a sidecar when it only supplies Codex UI metadata. Its presence does not make the shared workflow itself portable.

## Review before merging

Treat these as compatibility markers, not automatic errors:

| Marker | Typical host | Merge concern |
| --- | --- | --- |
| `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `$ARGUMENTS` | Claude Code | Codex may receive or interpret the text differently. Replace with host-neutral path discovery or document a host adapter. |
| Dynamic ``!`command` `` injection | Claude Code | Do not assume another host executes it. Prefer an explicit script invocation in the instructions. |
| `context`, `agent`, `background`, `hooks`, `paths`, `shell`, invocation flags | Claude Code | These fields can change invocation or permissions only in Claude Code. Preserve only with a deliberate host-specific exception. |
| `agents/openai.yaml`, Codex directives, Codex-only tool names | Codex | Claude Code may ignore metadata and may not provide the referenced capability. Keep optional metadata separate and make dependencies explicit. |
| Absolute home or workspace paths | Either | Replace with paths discovered at runtime. Never copy another machine's path into the canonical skill. |

Also inspect every script for host CLI names, permission assumptions, network access, environment variables, and unavailable packages. Matching files do not guarantee matching behavior when dependencies differ.

## Conflict policy

For the same normalized skill name with different hashes:

1. Compare all files, not only `SKILL.md`.
2. Identify shared intent, unique behavior, contradictory instructions, and host dependencies.
3. Propose the canonical result file by file.
4. Preserve unique useful behavior unless it conflicts with the user's chosen semantics.
5. Ask the user to choose when two behaviors are mutually exclusive or when adopting one changes permissions or external side effects.
6. Validate the staged result in both hosts where their CLIs are available.

Never make a byte-identical directory the goal when doing so would silently break one host. In that case, keep an explicit exception and report that the skill names are aligned but behavior or content is host-specific.
