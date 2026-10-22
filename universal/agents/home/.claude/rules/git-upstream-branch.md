# Git upstream branches

- A branch's upstream is its base (the branch its PR targets, e.g. `origin/main`, or its parent in a stack), so `@{u}..`, `git rebase` and `git status` measure against the base. Create branches from it: `git switch -c <branch> origin/main` or `git worktree add -b <branch> <path> origin/main`.
- `gh pr checkout` tracks the PR head instead; repoint with `git branch --set-upstream-to=origin/<base>`.
- `git push` (`push.default=current`) pushes to the same-named branch, so push without `-u`. For a PR from a fork, set `branch.<name>.pushRemote=<fork remote>`.
