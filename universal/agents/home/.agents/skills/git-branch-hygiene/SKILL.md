---
name: git-branch-hygiene
description: Commits and history on a feature branch. Use when committing on a non-default branch, before pushing, when rewriting a branch's history, or after its PR merges.
---

# Git branch hygiene

## Commits

- Every change is a new commit, corrections to earlier commits included. Refactors and behaviour changes go in separate commits.
- Rewrite history only when the unpushed commits **churn**: something tried and then undone, or the same lines reworked back and forth. Note the tip, run `git reset --soft @{push}` (`@{u}` if the branch was never pushed), recommit as a few commits that say what the branch keeps, then check that `git diff <old tip> HEAD` prints nothing.
- Pushed commits stay as they are unless the user asks to rewrite them. Then reset to `@{u}` instead, and push with `git push --force-with-lease`.

## After merge

- **Stacked branches:** while the merged branch's ref still exists, update `<base>` and run `git rebase --update-refs --onto <base> <merged> <top of stack>`. Point the bottom branch's upstream and its PR (`gh pr edit --base`) at `<base>`, and push each rebased branch with `git push --force-with-lease`.
- **Delete** the local branch with `git branch -d`, or `-D` for a squash merge once `gh pr view` shows it merged. Deleting writes `.git/config`, so run it outside the sandbox.
