---
name: tdd
description: Behavior-first testing, regression TDD and independent test oracles. Use for explicit TDD/test-first requests, integration testing, or a repository's required testing workflow.
---

# Behavior-first development and TDD

Protect observable behavior with independent expectations and fast feedback.
Read the project's glossary (`GLOSSARY.md`, or its established `CONTEXT.md`)
when present and the relevant ADRs; use the domain vocabulary. Follow an
existing `GLOSSARY-MAP.md` when several contexts have separate glossaries.
Repository rules and the user's explicit testing mode select the workflow.

## Choose the mode

- **Strict TDD:** when the user explicitly requests TDD, test-first or
  red-green-refactor. One focused failing behavior test, minimum implementation,
  then the same test GREEN before the next behavior. Refactor under GREEN tests
  when useful or in the repository's designated review stage.
- **Regression TDD:** for a bug, first reproduce the observable defect at the
  closest practical public/E2E boundary. Check why the test fails, fix the cause,
  then confirm the same test passes and affected contracts still hold.
- **Behavior-first slices:** otherwise, when the repository permits it. Specify
  the contract and independent examples first; implement one small coherent
  behavior with its related tests, then run the group. Code/test writing order
  is flexible. Do not turn the whole issue into one unverified batch.

Compilation failures, broken fixtures and infrastructure errors are not
behavioral RED. Add only a behaviorless contract scaffold when needed to run a
new test. Keep a later example that naturally passes; never damage production
code to manufacture RED. Pure refactoring uses existing GREEN tests, adding
characterization coverage only where protection is missing.

## Agree the contract and observations

A seam is the public boundary where behavior is observed. Seams and contracts
already agreed in the conversation, issue or repository guide need no repeated
confirmation. State the chosen boundary briefly. Ask only about unresolved
behavior or a new/materially changed architectural boundary; prepare the
concrete alternatives first. A repository's confirmation rules take precedence.

Before coding, map the issue's criteria to inputs, outcomes and existing
consumers that must migrate. Consider data types, errors and lifecycle ownership
together before choosing the first slice. Cover quantified states and transitions
without inventing requirements. Maintain one concise evidence map, not several
copies of the same checklist in messages and documents.

## Test quality, in every mode

Tests assert behavior through public interfaces and survive internal refactoring.
See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for boundaries.

- Expected values come from the specification, worked literals or independently
  approved examples, never a copy of the production calculation.
- Parameterized rows must reach the named state and assert its consequence.
  Changing a case label without changing the exercised path is not evidence.
- Observe the component that owns the requirement. A downstream event or client
  completion does not prove an earlier reservation, exported span or cleanup.
- For concurrency and resource ownership, enumerate terminal paths and illegal
  interleavings; use causal barriers and bounded waits. Keep required real E2E
  tests for streaming, cancellation, quotas, privacy and shutdown.
- Cleanup attempts every owned resource, retaining the first error and later
  failures as suppressed/equivalent evidence.
- Avoid private-method tests, internal collaborator mocks and duplicated
  implementation assertions. Mock external boundaries when needed.

## Approved scenarios

For deterministic parser, masking, header and error-mapping contracts, prefer
small fixtures pairing input with independently verified expected output.
Review the runner and its observation boundary first. Human approval establishes
the baseline when the expected behavior is not already unambiguously specified.
Keep actual output separate; an agent must not overwrite an approved baseline
just to make a failing scenario pass. Approve intentional behavior changes.
These fixtures complement lifecycle/E2E tests; they do not establish race safety.

## Feedback and closure

Run the narrow affected tests and cheap lint after a coherent slice. Check old
contract consumers before the broad build. Repeat expensive checks only after
relevant changes, failures or an explicit task requirement; retain the required
final regression evidence. Report actual commands/results and why RED failed
where RED was required. Do not count test names or report flags as proof.

Mutation testing is an optional, risk-directed check of regression sensitivity,
not a default per-slice gate or proof that business requirements are correct.
Use the repository's dedicated command/skill when requested or authorized.
