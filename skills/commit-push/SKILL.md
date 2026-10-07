---
name: commit-push
description: >-
  Commit and push the current task changes directly, using caveman-commit for
  the message. Use when the user asks to commit and push or invokes
  /commit-push or $commit-push. Do not start no-mistakes, create a PR, or add
  validation gates unless the user explicitly requests them.
---

# Direct commit and push

Treat "commit and push" as authorization for the ordinary Git mutations it
names, without expanding the workflow.

1. Inspect `git status`, the current branch, its upstream, and the relevant
   diff. Preserve unrelated user changes and stage only the current task's
   files. If the worktree is already clean with unpushed commits, skip staging
   and committing.
2. Use the installed `caveman-commit` skill to generate a terse Conventional
   Commit message. Follow the repository's history, omit a body when the
   subject is self-explanatory, and never add AI attribution or a co-author.
3. Before committing, run `git diff --cached --check` and confirm no unrelated
   files are staged. Do not add reviews, tests, lint, or other validation unless
   the user asked for them; rely on validation already completed in the task.
4. Commit on the current branch. Do not create a feature branch, rebase, amend,
   squash, or rewrite history unless the user or repository explicitly requires
   it.
5. Push normally. Use the existing upstream when configured; otherwise verify
   the intended remote and run `git push -u <remote> <current-branch>`. Never
   force-push without explicit authorization.

Do not invoke `no-mistakes`, open a pull request, wait for CI, or launch another
delivery pipeline merely because the user requested commit and push. Those are
separate actions requiring an explicit request.

If push is rejected, authentication is unavailable, the remote is ambiguous,
or a non-fast-forward update would require history changes, stop and report the
exact blocker instead of forcing or broadening the operation.

On success, report the commit hash, subject, remote branch, and whether the
worktree is clean.
