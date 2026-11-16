# Git upstream branches

- A branch's upstream is its base (the branch its PR targets, e.g.
  `origin/main`, or its parent in a stack), so `@{u}..`, `git rebase` and
  `git status` measure against the base.
- The sandbox blocks writes to `.git/config`, and `git branch --set-upstream-to`
  / `git branch -u` run outside it. So create the branch without tracking, then
  set the upstream in a separate Bash call (not chained with `&&`, or it stays
  sandboxed):
  1. `git switch --no-track -c <branch> origin/main` or
     `git worktree add --no-track -b <branch> <path> origin/main`
  2. `git branch --set-upstream-to=origin/main <branch>`
- `gh pr checkout` tracks the PR head instead; repoint with
  `git branch --set-upstream-to=origin/<base>`. Repoint the same way whenever
  the base changes, such as a stacked PR retargeted with `gh pr edit --base`.
- Delete a merged local branch with `git-branch-merged -d <branch>` (the
  `git-branch-hygiene` skill has when and how). It runs outside the sandbox only
  as a plain command: one branch per Bash call, nothing chained, no `git -C`.
  `git branch -d` runs sandboxed, so it deletes the ref but leaves the branch's
  section in `.git/config`.
- `git push` (`push.default=current`) pushes to the same-named branch, so push
  without `-u`. For a PR from a fork, set
  `branch.<name>.pushRemote=<fork remote>`.
