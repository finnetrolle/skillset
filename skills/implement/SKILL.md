---
name: implement
description: Route and implement one existing implementation-ready project issue by exact work-item ID or unique title. Use only when explicitly invoked as $implement; do not use for drafting issues, epics, general coding requests, or untracked work.
---

# Implement

Implement one tracked issue and hand its evidence to verification. Report the issue
closed only after all required verification and repository completion steps have
finished. Select the least expensive model that preserves the required quality.

## Input

Treat the text after `$implement` as one exact work-item ID or unique issue title, for example `$implement VIG-45-23`.

- Require exactly one issue. Do not implement an epic or combine several work items.
- Resolve an exact ID by searching issue files recursively for either an exact `# <ID>:` heading or the project's exact `**ID:** \`<ID>\`` metadata form. Require exactly one matching issue file. Then verify that a standalone issue is registered directly, or that a child issue is listed by its registered parent epic. Accept a title only when it has one unique issue-file match.
- If the issue is missing or ambiguous, stop and show the matching candidates. Never guess.
- Proceed only when the issue status is `Ready for implementation` or `In progress` and every hard dependency is `Done`.
- For `Draft`, `Blocked`, or `Done`, stop with the concrete reason and the appropriate next action. Do not silently change the status or scope to make the issue executable.

## Execution boundary

Resolve the issue and its ready state, then choose the risk route before coding.
Default to implementing in the current task. A single issue does not require a
dispatcher/worker pair when the current agent can execute it at the needed
quality. Read the repository guide, issue, linked epic, hard prerequisites and
relevant normative sections once; keep a compact contract/evidence map.

Before coding, read the shared
[acceptance evidence contract](../../../.agents/skills/verify-changes/references/acceptance-evidence.md).
Check how the exact agreed issue text and user amendments can be recovered for
verification and completion. Record the source path, committed revision when
available, and explicit amendments in the manifest. If the only agreed issue
source has uncommitted changes, preserve its exact text in the durable evidence
package, keep the issue intact, and record any Git-recoverability requirement
as a closure blocker now.
This does not by itself stop safe implementation; resolve the blocker before
marking the issue closed or removing its source.

The route below is a model recommendation, not evidence that a model switch
occurred. Follow an explicit user model choice. If current settings are known
to fit, work inline. If settings are unknown, do not claim a specific model or
spawn merely to learn them; use the configured agent and disclose the limit.
When a known model mismatch actually requires a switch, prefer a supported
main-task switch; otherwise this skill authorizes exactly one implementation
worker. Do not spawn a worker solely to repeat the current model and effort.

## Route selection

Before selecting a model, check the models and reasoning efforts exposed by the
current `spawn_agent` tool. That runtime list is authoritative for worker
availability; models listed only for task creation are not necessarily available
to subagents. The mapping below is a routing policy, not a verified price table.

Assess both impact and implementation risk before choosing a route:

- Read explicit priority, severity, milestone, release-gate, customer-impact, and blocking metadata when present. Do not invent missing metadata.
- Treat changes to normative requirements, public contracts, mandatory release evidence, compliance or security claims, and work-item dependency/status semantics as high impact even when they are documentation-only.
- Critical impact selects `critical`. High impact selects at least `standard`. Unknown impact on production behavior selects at least `standard`.

Then choose one route from the table. Use the highest route whose conditions apply.

| Route | Model and effort | Use when |
|---|---|---|
| `fast` | `gpt-5.6-luna`, `low` | Exact mechanical change with no production behavior change and no normative or release impact, such as a non-normative broken link or deterministic non-semantic metadata formatting. It must not change work-item status/dependencies, requirements, compliance/security claims, public/runtime contracts, or release evidence. |
| `balanced` | `gpt-5.6-terra`, `medium` | Narrow, isolated, reversible change with explicit acceptance criteria and local tests; no critical-risk marker applies. |
| `standard` | `gpt-5.6-terra`, `high` | Default for production code, multi-file behavior, integration work, non-trivial tests, or ordinary implementation uncertainty. |
| `critical` | `gpt-6-astra`, `xhigh` | Concurrency, synchronization, streaming/backpressure, durability/persistence, security/privacy/auth, schema or data migration, public API/protocol compatibility, process lifecycle, data-loss risk, architecture boundaries, cross-process E2E, or a large/ambiguous blast radius. |

This mapping was checked against the worker tool on 2026-09-08: it exposes
`gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`, and `gpt-5.5`.
Astra is described there as the most capable model for complex, demanding work,
so it owns `critical`. Sol and GPT-5.5 remain available but are not selected by
these default routes. Recheck the live tool rather than treating this snapshot
as permanent availability.

Routing invariants:

- Any production behavior change is at least `balanced`; when unsure, use `standard`.
- Any critical marker makes the route `critical`, even if the diff is expected to be small.
- Multiple modules, several interacting acceptance criteria, or unclear ownership make the route at least `standard`.
- A high word count, many checklist items, or words such as `all` and `deterministic` are evidence to inspect, not automatic promotion by themselves.
- Resolve ties upward. Never choose a cheaper route merely because the parent task already uses that model.
- Confirm that the selected model supports the exact effort before spawning.
  If either is unavailable, use the fallback below instead of silently
  substituting another model or lowering the route.

Report one concise route line, distinguishing recommended and verified settings:

```text
Route: <route>; execution: inline | worker <verified model/effort>; reason: <risk>.
```

## Implement

Follow the repository testing mode and the loaded `tdd` skill. Plan contracts,
independent examples, old consumers and ownership before the first slice. Run
cheap lint and affected old/new tests early, then the required final checks.
Preserve unrelated changes. Apply the repository's work-item completion
protocol only after the required verification gates have passed; completion
edits may change inputs, so recheck applicability before reporting closure.
Some projects remove completed issues after transferring requirements; keep
the exact agreed source recoverable for verification and in Git before such
removal when the project requires it.

For the exceptional worker route, use `fork_turns="none"` and a compact prompt:
repository, issue/source revision, route, applicable instructions, acceptance and
non-goals, baseline changes, testing mode, required validation and handoff ledger.
Do not invoke `$implement` recursively. The worker owns implementation and the
verification handoff. Report closure only if required independent verification
and the repository completion protocol also finish; the parent does not
duplicate exploration or coding.

Use completion/blocker notifications when supported. Do useful independent work
while waiting. If polling is required, use one bounded wait aligned with the
outer tool yield; do not layer short waits or request routine heartbeat messages.
Send a focused follow-up only for a concrete blocker or missing requirement.
Inspect the final diff/evidence enough to verify completeness, without creating
another full review role. Dedicated independent review remains separate.

Use the repository durable runner for long commands when available. Preserve
each completed check's reports, including causal RED, before another command
can overwrite them. Pass the saved manifest, exact run IDs and remaining
completion actions to verification; a chat summary is not the evidence store.
Do not recreate completion proof by rerunning a finished command after an
interactive session expires.

## Verification handoff

Before marking implementation ready for verification, reread the complete issue,
its non-goals, and the full diff, then return a handoff ledger with one row per
acceptance criterion and non-goal:

- the distinct production or runtime path exercised;
- the public observation that proves the requirement;
- the independent oracle used by the assertion;
- the exact command and result that produced the evidence, with a link to its
  preserved report or durable run artifact.

For structural non-goals and documentation criteria, use concrete diff/search,
link/render or validator evidence; mark runtime/oracle fields inapplicable with
a reason. Behavioral criteria still require the real path, public observation
and independent oracle. Do not invent runtime tests for structural assertions.

A test name, parameter label, comment, hard-coded pass flag or count, duplicated
production calculation, or observation of a different component is not evidence
for the named requirement. Parameterized rows count separately only when their
setup reaches distinct required states or transitions and asserts the
case-specific consequence.

The implementer must also report concisely:

- searches performed before adding a comparator, invariant, report calculation,
  launcher, polling helper, raw HTTP fixture, or lifecycle helper, and whether a
  canonical implementation was reused;
- the old and new contract vocabulary searched across production code, tests,
  KDoc/Javadoc, current docs, normative specs, and dependent work items;
- for stateful, concurrent, resource-owning, or cross-process work, a lifecycle
  matrix covering owner, terminal event, observable cleanup, and failure path;
- the final diff scope and every retained file that is not directly owned by the
  issue.

Do not mark implementation ready for verification while any ledger row lacks
evidence, a quantified case is only a label, lifecycle ownership is incomplete,
a stale contract remains or scope is unresolved. Correct the gap in the current
implementation context. Run the repository work-item validator after the final
completion/removal update if that update is performed.

## Fallback

If a known required model switch cannot be made inline or through the available
worker tool, report the exact route and limitation. Ask for a relaunch only when
the known mismatch prevents appropriate execution. Do not modify profiles or
silently claim that automatic routing occurred.

## Final response

Lead with the exact state: implementation ready for verification; verified but
closure pending; issue closed after verification and the repository completion
protocol; or blocked with the concrete reason. Never call a ready implementation
a closed issue. Name the responsible next phase and remaining actions from the
evidence manifest. Include the selected route, a compact change summary,
validation results, and material risks. Do not expose internal chain-of-thought
or repeat the entire issue.
