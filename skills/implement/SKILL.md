---
name: implement
description: Route and implement one existing implementation-ready project issue by exact work-item ID or unique title. Use only when explicitly invoked as $implement; do not use for drafting issues, epics, general coding requests, or untracked work.
---

# Implement

Implement one tracked issue and hand its evidence to verification. Report the issue
closed only after all required verification and repository completion steps have
finished. Use execution settings capable of meeting the required quality.

## Input

Resolve one exact existing issue or unique title from the source the user names.
Read its full accepted contract, non-goals, hard prerequisites and repository
completion rules. Do not infer readiness merely from an identifier or commit.

Use the repository's issue-tracker adapter when it has one. For a local
`spec/WORK_ITEMS.md` registry, read [the local work-item adapter](references/work-items.md).
Do not force that file layout or status vocabulary onto GitHub, GitLab or another
tracker. If the issue is missing, ambiguous, not ready or blocked, report the
specific gap; never change its status or requirements just to make it executable.

## Execution boundary

Resolve the issue and its ready state, then choose the risk route before coding.
Default to implementing in the current task. A single issue does not require a
dispatcher/worker pair when the current agent can execute it at the needed
quality. Read the repository guide, issue, linked epic, hard prerequisites and
relevant normative sections once; keep a compact contract/evidence map.

Before coding, read the shared
[acceptance evidence contract](../verify-changes/references/acceptance-evidence.md).
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

Assess impact and implementation risk against the issue and repository rules.
Read [the risk guide](references/risk-routing.md) when deciding whether the current
execution settings fit. The host's exposed models, efforts and tools are the
source of truth; never claim that a recommended setting has actually been applied.
Honor the user's explicit model and budget choices.

Prefer the current agent when it can meet the required quality. A known mismatch
can justify a supported switch or the exceptional single implementation worker
below. Do not create a dispatcher/worker pair merely to repeat current settings.
No model names or prices in this skill are a permanent routing table.

Report one concise line when routing is relevant:

```text
Risk: <mechanical | bounded | standard | critical>; execution: inline | worker;
settings: verified <model/effort> | current settings unverified; reason: <risk>.
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
evidence manifest. Include any relevant routing decision, a compact change summary,
validation results, and material risks. Do not expose internal chain-of-thought
or repeat the entire issue.
