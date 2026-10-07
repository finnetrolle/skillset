# Local work-item adapter

Use only when the repository defines `spec/WORK_ITEMS.md` or the same contract in
its guide. Follow that repository's exact directories, statuses and ID syntax.

For the established five-status convention:

- Resolve an exact `# <ID>:` heading or `**ID:** `<ID>`` metadata recursively.
- Require one unique matching issue and its registration, directly or through
  its parent epic. A unique title is an alternative to the exact ID.
- Proceed for `Ready for implementation` or `In progress`, with all hard blockers
  `Done`; do not silently promote `Draft`, `Blocked` or `Done` work.
- Preserve the agreed source and evidence before any completion protocol removes
  the issue. Apply registry, epic and issue status changes together as specified.
- Run the repository's work-item validator after completion changes.

These conventions adapt the portable implementation workflow. They do not
establish the issue-tracker contract in a repository that never adopted them.
