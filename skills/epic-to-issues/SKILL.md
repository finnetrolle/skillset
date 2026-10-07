---
name: epic-to-issues
description: "Turn oversized plans, specs, or issues into linked epics and independently grabbable implementation issues using mind-map discovery, tracer-bullet slicing, dependency graphs, estimates, and approval before publication. Use when work needs decomposition, epic creation, issue splitting, effort estimation, or restructuring of a Markdown backlog. Do not use merely to implement an already-ready issue."
---

# Epic to Issues

Convert uncertain scope into a navigable discovery map, then convert that map into a delivery graph of small, complete outcomes. Preserve the epic as the normative contract. Do not implement production code while decomposing it.

Read [the slicing guide](references/slicing.md) before choosing issue boundaries.

## Workflow

1. Gather context before proposing boundaries.
   - Read repository instructions, the target item, linked specs, ADRs, glossary, and backlog conventions.
   - Sample adjacent issues to preserve naming, status, estimate, and acceptance style.
   - Inspect code only as needed to confirm public seams, dependencies, and realistic effort.
   - Identify the tracker. Prefer its native API or connector when available.
2. Build a discovery mind map.
   - Root: user or system outcome.
   - Branches: capabilities, decisions, integrations, risks, migrations, and evidence.
   - Leaves: independently verifiable outcomes or unresolved decisions.
   - Keep relationships visible. Do not replace the map with a flat brainstormed list.
3. Classify each branch using the slicing modes in the guide.
   - Default to vertical tracer bullets.
   - Use prefactoring only when it unlocks a concrete slice.
   - Use expand, migrate, contract for wide refactors.
   - Separate irreversible or human-owned decisions from implementation.
   - Permit a module-level slice only at a stable public seam.
4. Draft the delivery graph.
   - Each implementation issue delivers one complete, demonstrable behavior.
   - Each issue must fit one fresh agent context and normally one reviewable change.
   - State acceptance criteria at the consumer or public seam.
   - Include parent, blockers, requirements covered, non-goals, estimate range, and confidence.
   - Add a blocker edge only for a hard gate. Preferred order is not blocking.
   - Reject cycles and compute the frontier: non-done issues whose blockers are done.
5. Run the proposal gate before mutation.
   - Show epic outcome, mind map, proposed issues, delivered behavior, mode, blockers, estimates, frontier, open decisions, and intended file or tracker changes.
   - Ask for approval unless the user already explicitly authorized applying this exact decomposition now.
   - Resolve decisions that would materially change issue boundaries before publication.
6. Publish after approval.
   - Create one tracker item or Markdown file per issue.
   - Keep the epic concise but normative: outcome, scope, decisions, map, completion criteria, and linked child summary.
   - Preserve the original source by moving or linking it. Do not silently delete, close, or rewrite history.
   - Use native epic, subissue, and blocker relationships when the tracker supports them.
7. Validate after publication.
   - Confirm every normative requirement is covered or explicitly out of scope.
   - Recheck issue independence, verticality, estimates, hard blockers, DAG, and frontier.
   - Report created or moved items, validation result, frontier, and unresolved decisions.

## Local Markdown adapter

If `spec/WORK_ITEMS.md` exists, treat it as the project adapter, not as generic truth:

- Follow its exact directories, IDs, statuses, estimate units, and completion protocol.
- Use stable relative links. Give each child exactly one parent epic.
- Treat the issue status as source of truth. Update epic checkbox, mirrored status, and registry counter in the same change set.
- List epic children in dependency order.
- Run:

```bash
python3 <skill-directory>/scripts/validate_work_items.py <repository-root>
```

The bundled validator targets the five-status `WORK_ITEMS.md` convention used by Vigilant. If another repository defines a different Markdown schema, follow that repository and validate it with an adapted check instead of forcing this schema.

## Stop conditions

Pause publication when the intended outcome, normative source, ownership of a decision, or irreversible migration boundary is unresolved. Continue discovery and present the precise decision needed. Do not manufacture certainty by hiding it inside an implementation issue.
