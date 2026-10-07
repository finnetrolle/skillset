---
name: arch-review-to-epic
description: "Architectural review of a codebase against its own normative spec, followed by conversion of the review findings into a tracked epic and independently grabbable issues. Use when the user asks for an architecture/architectural review of a project or codebase ('архитектурное ревью', 'проанализируй проект', 'review the architecture'), or wants review findings turned into an epic and issues ('создай эпик из замечаний'). Covers both halves: the review itself and the remediation backlog. Do not use for single-PR code review or implementing an already-ready issue."
---

# Arch Review to Epic

Review the architecture against the project's own normative sources, then convert every finding into tracked, decomposed, grabbable work. One conversation, two phases: review produces evidence-backed findings; epic creation consumes them without dropping any.

## Phase A: Architectural review

### 1. Gather context before judging

Read, do not sample:

- Repository instructions (CLAUDE.md, CONTRIBUTING) - they encode local constraints.
- The normative source: spec/, requirements, ADRs. This is the yardstick. A finding without a normative reference is judgment and must be labeled as such.
- All production code (for a small codebase) or the modules in scope plus their callers (for a large one).
- All tests - to know what is verified versus merely claimed.
- Build config, debt registries (e.g. sonar_problems.md), and the work-item registry (spec/WORK_ITEMS.md, backlog, tracker).
- Runtime/delivery artifacts when they exist (Dockerfile, CI, logging config).

### 2. Review dimensions

Evaluate in this order; each dimension yields findings of a distinct kind:

1. **Spec conformance.** For every requirement declared in scope for the current stage: implemented? unimplemented? partially implemented? The diff between declared scope and actual scope is usually the biggest finding.
2. **Core path correctness.** Data path, error paths, edge cases, protocol rules (e.g. hop-by-hop headers, streaming, backpressure).
3. **Verification gaps.** Behaviors the spec demands as acceptance criteria but that no test exercises (especially E2E/streaming/cancellation/security-leak classes). A spec criterion without a test is a finding even when the code looks correct.
4. **Operational posture.** Timeouts, health probes, graceful shutdown, observability (metrics/traces/structured logs), secret hygiene.
5. **Future-stage readiness.** Whether current seams support the next stage without rework - praise or warn, do not demand premature abstraction.
6. **Process gaps.** Scope items that are neither implemented nor tracked in the backlog registry. Untracked gaps are how a stage gets declared "done" while incomplete.

### 3. Findings discipline

Every finding must carry:

- **What** and **why it is a problem** (one sentence each).
- **Where**: `file:line` or the absence of a file/test.
- **Normative source**: spec requirement ID, repo instruction, or an explicit "judgment, no spec" label.
- **Class**, one of: `code-defect` (implemented wrong), `missing-behavior` (spec'd, not implemented), `unverified` (implemented, no test), `untracked` (spec'd, absent from backlog), `nit` (minor), `decision` (human-owned choice).

This classification drives Phase B: `code-defect`/`missing-behavior`/`unverified` become implementation issues; `untracked` becomes registry plus issues; `nit` becomes optional cleanup; `decision` becomes a decision item, never hidden inside an implementation issue.

Never state a library default you are not sure of. Phrase as "not configured explicitly; library defaults apply; spec demands explicit policy".

### 4. Review output format

Deliver in this order:

1. **Verdict** - one paragraph: is the architecture sound, where are the real risks.
2. **What is good** - name concrete decisions worth keeping; protects them from refactor churn.
3. **Findings by severity** - a table (severity, finding, where, requirement ID), critical first. Group nits separately.
4. **Process gaps** - backlog registry holes.
5. **Readiness for next stage** - which seams will hold, which will break.
6. **Recommendations** - ordered by leverage and by what unblocks other work, not by severity alone.

## Phase B: Epic and issues from findings

### 5. Follow the project's tracker adapter

If a work-item convention exists (spec/WORK_ITEMS.md or similar), treat it as the local adapter: its directories, IDs, statuses, estimate units, link format, and completion protocol override generic habits. Sample one existing epic and two child issues and copy their structure field-by-field before writing anything. If the `epic-to-issues` skill is installed, follow its slicing discipline (tracer bullets, one behavior per issue, hard gates only).

### 6. Mapping rules

- One finding class maps to one issue class:
  - `missing-behavior` + its `unverified` companion test gap -> one vertical issue per observable behavior (implementation + its E2E test together).
  - Pure `unverified` (code correct, test absent) -> test-only issue; if the test later exposes a real defect, split the fix into its own issue rather than expanding scope.
  - `untracked` -> registry row plus the issues that cover the scope.
  - `decision` -> decision item inside the issue that needs it, with a recommended baseline; a separate decision issue only when the choice changes issue boundaries or has a different owner.
- Group issues into mind-map branches by concern (reliability, verifiability, observability, operations, performance), not by code layer.
- No finding is silently dropped. Every finding ends up covered by an issue, explicitly out of scope, or explicitly downgraded to a nit with the user's knowledge. Include a finding-to-issue coverage matrix in the final report.

### 7. Dependency hygiene

- Blocker edges only for hard gates (acceptance impossible until the blocker is done). Preferred order is not blocking.
- Express preferred order in prose in the epic ("prefer X before Y because Z"), never as an ID inside a dependency field - backlog validators commonly regex IDs out of those lines and will report false cycles. Keep dependency fields to real IDs or a bare "none".
- After publication, run the project's validator if one exists; fix until clean.

### 8. Publication

- Epic document: context (review date, source), decomposition map, children checklist with mirrored statuses, goal, requirements list, non-goals, open decisions each localized to its owning issue with a recommended baseline, acceptance criteria, and (if the convention uses them) an ambiguity report.
- Status honesty: epic is `Ready for implementation` only when remaining decisions are local to issues and cannot change boundaries; otherwise `Draft` with the blocking decision named.
- Issues: status, parent link, branch, dependencies, estimate range plus confidence, delivered outcome, acceptance criteria tied to requirement IDs, non-goals, recommended decisions with baselines.
- Update the registry row in the same change set.
- Additive changes only; never rewrite existing backlog history.

### 9. Final report

Report: created files/items, validator result, frontier (issues grabbable now), the finding-to-issue coverage matrix, and unresolved decisions with owners.

## Stop conditions

- Pause Phase B when a review finding implies an irreversible or human-owned decision that would redraw issue boundaries; present the decision instead of guessing.
- Pause Phase A halfway only if the normative source does not exist - then agree with the user what yardstick to review against before judging.
- Never implement production code while running this skill; it produces a review and a backlog, nothing else.
