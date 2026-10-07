---
name: cavecrew
description: >-
  Choose and brief subagents for code investigation, bounded 1-2 file edits,
  and focused review with compact, evidence-bearing results. Includes portable
  investigator, builder and reviewer role instructions for the host's available
  delegation tools. Use for "delegate to subagent", "use cavecrew",
  "spawn investigator/builder/reviewer", "save context", or "compressed agent output".
---

# Cavecrew

Delegate bounded work and return short results that preserve evidence,
uncertainty and verification status. Roles are included in this package;
`cavecrew-*` names are role labels, not assumed installed agent types.

## Choose the role

| Task | Route |
|---|---|
| Locate definitions, callers, uses or tests | [investigator](references/investigator.md), read-only |
| A clear edit in 1-2 known project files | [builder](references/builder.md) |
| Find actionable bugs/risks in a diff, branch or specified files | [reviewer](references/reviewer.md), read-only |
| Already-known one-line answer | Answer directly |
| New feature, 3+ file edit, cross-cutting refactor | Main thread or a general agent with adequate scope |
| Architecture options or a deep explanation | Main thread or a general agent; request the necessary rationale |

A short report is the goal, not a fixed token reduction. Do not claim measured
savings without actual comparable measurements.

## Use the host's available delegation

1. Check the tools actually exposed in the current session and applicable
   delegation rules. Use Codex or Claude Code's available agent mechanism;
   do not invent a tool, registered preset or model name.
2. Read the selected role and its [shared contract](references/shared.md).
   If an existing named preset is available, use it only when its instructions
   meet this role's contract. Otherwise give a general agent the role instructions
   as its assignment. A label such as `cavecrew-builder` may name the task; pass
   it as an agent type only if that type is actually registered.
3. Give the worker the concrete objective, repository/working directory, allowed
   files and mutations, relevant requirements, raw artifacts, and the expected
   result. State whether the workspace is shared or isolated. If the worker
   can read this package, point to the absolute selected role path; otherwise
   include the role and shared contract text in its prompt.
4. Inherit the current/default model settings unless an explicit user choice or
   applicable instruction calls for an available override. This package requires
   no Claude plugin hooks, frontmatter patching or `CAVECREW_*_MODEL` variables.
5. Wait for completion using the host's available mechanism. Reuse a worker
   when appropriate. Inspect the result and any changed files before handoff.

When delegation is unavailable or disallowed, do the scoped work inline using
its role contract and tell the user if that affects the requested outcome.
Do not require installation of another agent package just to use these roles.

## Task brief

Include only context that changes the worker's decisions:

```text
Role: <absolute role-reference path, or included role + shared instructions>
Task: <concrete result>
Workspace: <absolute directory; shared or isolated>
Scope: <files, symbols, diff/base revision; permitted mutations>
Requirements: <user contract and applicable project rules>
Evidence: <raw inputs, reproduction or observations; known limitations>
Return: <role output contract; verification and unresolved matters>
```

For an independent review, supply requirements and raw changes rather than an
expected verdict. Do not steer the reviewer toward the builder's conclusions.

## Chains and parallel work

- Locate -> edit -> review: investigator identifies sites, main thread chooses
  1-2 files, builder changes them, reviewer inspects the actual resulting diff.
- Known site: brief the builder directly when discovery is unnecessary.
- Broad read-only investigation: use 2-3 scouts on distinct questions when
  delegation is permitted and the work benefits from parallel execution.

Assign one writer to each shared file. Independent readers can run in parallel;
wait for an edit to finish before reviewing its resulting diff. Do not split a
coupled 5-file change into builders just to bypass the builder's scope limit.

## Main-thread handoff

Keep worker findings traceable to files/lines and relevant observations. Preserve
unanswered questions, partial results and failed or skipped checks. Re-reading
changed text is not a passing build, test or behavioral verification.

Explain cryptic fragments when presenting the result to the user. Expand beyond
one line when security, architecture, irreversible actions or unfamiliar context
need a rationale. Compression must not turn uncertain evidence into certainty
or substitute for the requested depth of work.
