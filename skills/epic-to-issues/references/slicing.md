# Slicing guide

Use this guide after gathering project context and before presenting the proposal.

## Discovery map versus delivery graph

The mind map answers, "What is inside this problem, and how is it related?" The delivery graph answers, "What complete result can be shipped next, and what truly blocks it?"

Do not publish every mind-map leaf unchanged. A discovery branch often follows architecture, while a useful implementation issue usually crosses several layers to prove one behavior.

## Slicing modes

| Mode | Use when | Shape |
|---|---|---|
| Tracer bullet | A product or system behavior can be exercised end to end | Smallest real path from input to observable result |
| Prefactoring | A narrow structural change is a hard prerequisite for one named slice | Refactor, then immediately deliver the unlocked slice |
| Expand, migrate, contract | A shared interface or data shape has many consumers | Add compatibility, migrate bounded batches, remove old path |
| Decision | An irreversible, costly, or human-owned choice is unresolved | Evidence, options, recommendation, named decision owner |
| Module seam | A library or isolated component has a stable public contract | One consumer-visible capability tested through that contract |

Research is not automatically a separate issue. Keep reversible discovery inside the implementation issue unless it needs a different owner, has an independent deliverable, or blocks several branches.

## Tracer-bullet test

An implementation issue is ready only when all are true:

1. It names a consumer-visible or operator-visible result.
2. Acceptance can be demonstrated through one public seam.
3. It crosses every necessary layer for that result, even if each layer is thin.
4. It can merge without waiting for a later sibling to become meaningful.
5. Its non-goals prevent adjacent scope from leaking in.
6. A capable agent can finish it in one fresh context window.
7. The estimate is small enough for one reviewable change under the project's sizing convention.

Split again when the issue contains independent outcomes, several unrelated test seams, hidden decisions, a multi-team handoff, or a large migration batch.

## Horizontal-slice smell

Review a proposed issue when its title is only a component noun such as "API", "parser", "database", "pipeline", or "UI". Other warning signs:

- Acceptance lists internal files or classes but no delivered behavior.
- The issue only prepares infrastructure for unnamed future work.
- All useful behavior appears only after several sibling issues finish.
- Requirements are grouped by technical layer rather than by user story.

A horizontal title is not automatically wrong. It can be correct for prefactoring, expand-migrate-contract, a decision, or an isolated module seam. Label that exception explicitly and name what it unlocks.

## Dependency rules

- `A blocked by B` means A cannot meet its acceptance criteria until B is done.
- Do not encode preferred sequence, shared topic, or convenient staffing as blocking.
- Keep cross-epic blockers explicit.
- Reject cycles.
- The frontier contains ready or in-progress, non-done issues whose blockers are done.
- Put independent frontier items first in the proposal so parallel work is visible.

## Effort estimates

Estimate a range in the project's unit. Include implementation, tests, review fixes, documentation required by acceptance, and migration work. Exclude named dependencies and optional follow-ups.

Attach confidence:

- High: known seam, precedent exists, no open decisions.
- Medium: limited unknowns with bounded investigation.
- Low: missing decision, unfamiliar integration, or unclear migration scale.

Low-confidence implementation work is usually evidence that a decision item or another decomposition pass is needed.

## Proposal format

```text
Epic
  Title:
  Delivered outcome:
  Scope:
  Non-goals:
  Completion evidence:

Mind map
  root
  +-- branch
      +-- leaf

Issues
  ID | Title | Delivers | Mode | Blocked by | Requirements | Estimate | Confidence

Frontier
  IDs that can start now

Open decisions
  Decision | Owner | Impact on decomposition

Planned mutations
  Items to create, move, or link
```

## Issue contract

Every published issue should contain:

```text
Parent epic
What this issue delivers
Acceptance criteria
Blocked by
Requirements covered
Non-goals
Estimate and confidence
Validation or demo seam
```

Prefer behavior and constraints over implementation recipes. Mention exact files or symbols only when they are normative boundaries, migration targets, or necessary evidence from the repository.

## Final semantic audit

Before publishing, ask:

- Does the epic retain every normative rule that children depend on?
- Is every requirement covered exactly somewhere, or deliberately shared and explained?
- Are decisions separate from code when ownership differs?
- Are blocker edges hard gates and acyclic?
- Can each implementation issue be reviewed and demonstrated alone?
- Does the frontier expose safe parallel work?
- Would a new agent understand each issue without reconstructing the entire decomposition conversation?
