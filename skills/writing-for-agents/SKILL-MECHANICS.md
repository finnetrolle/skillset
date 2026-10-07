# Skill mechanics

Read this reference when changing skill discovery, frontmatter or routing.
The general writing guidance lives in [SKILL.md](SKILL.md).

## Preserve invocation policy

Skill hosts have different controls. Inspect the target host and the existing
metadata before changing invocation. Preserve the current policy unless the
user requests a change. Keep a precise description even for explicit invocation.

- In Codex, automatic selection is allowed by default. An explicit-only skill
  uses `policy.allow_implicit_invocation: false` in `agents/openai.yaml` and
  remains available through `$skill-name`. Preserve the other fields in that
  file. See the installed `skill-creator` reference for the supported schema.
- In Claude Code, `disable-model-invocation: true` in `SKILL.md` prevents
  automatic invocation. That field does not substitute for Codex policy.
  See [the Claude Code skills documentation](https://code.claude.com/docs/en/skills).
- If another host has different controls, verify them in its documentation;
  do not infer a universal discovery or token-cost rule from either host.

Discovery policy and execution authorization are separate. A discoverable
release skill can still require approval immediately before publishing.
Neither a description nor a reference to another skill authorizes side effects.

## Split for independent use

Split a skill when a distinct workflow needs independent discovery, or when
conditional detail can be read separately. Keep substantial mode-specific
instructions in references so ordinary use need not load all modes.

A shared reference may live in one package and be linked relatively. Declare
that package dependency so installation retains it. Reading a reference does
not require changing the referenced skill's invocation policy.

## Routers

A router is useful when users repeatedly need help choosing among several
workflows. Keep the entrypoints few and the routing conditions concrete. Respect
each destination's explicit invocation requirements and the actual tools exposed
by the host. Do not invent a `Skill` tool where the host only supports file reads.
