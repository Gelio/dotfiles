# Git upstream branches

- A branch's upstream is its base (the branch its PR targets, e.g. `origin/main`, or its parent in a stack), so `@{u}..`, `git rebase` and `git status` measure against the base.
- The sandbox blocks writes to `.git/config`, and only `git branch --set-upstream-to` / `git branch -u` run outside it. So create the branch without tracking, then set the upstream in a separate Bash call (not chained with `&&`, or it stays sandboxed):
  1. `git switch --no-track -c <branch> origin/main` or `git worktree add --no-track -b <branch> <path> origin/main`
  2. `git branch --set-upstream-to=origin/main <branch>`
- `gh pr checkout` tracks the PR head instead; repoint with `git branch --set-upstream-to=origin/<base>`.
- `git push` (`push.default=current`) pushes to the same-named branch, so push without `-u`. For a PR from a fork, set `branch.<name>.pushRemote=<fork remote>`.
