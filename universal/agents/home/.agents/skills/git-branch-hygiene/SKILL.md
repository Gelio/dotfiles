---
name: git-branch-hygiene
description: Fixup commits and autosquash on a feature branch. Use when committing on a non-default branch, before pushing or opening a PR, after a PR merges, or when tidying a branch's history.
---

# Git branch hygiene

## While working

- Correct an earlier commit on the branch with `git commit --fixup=<sha>`.
- Refactors and behaviour changes go in separate commits. Split an existing mixed commit only when asked.

## Before push

1. **Base:** `@{u}`. Without one, the fork point in `git log --oneline --graph --decorate --all`; ask only if it's unclear.
2. **Start:** `@{push}` if the branch was pushed, else the base. Pushed commits stay as they are, so a fixup of one is left unsquashed: tell the user. When the user asks to rewrite them, start from the base and finish with `git push --force-with-lease`.
3. **Squash:** note `git rev-parse HEAD`, then run `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash --keep-base <start>` (no editor opens, so `-i` works; `--keep-base` keeps the branch where it forked). Resolve conflicts yourself; ask only when the resolution is unclear.
4. **Check:** `git diff <old tip> HEAD` prints nothing. Any output means a conflict was resolved wrongly; fix it.
5. **Show** `git log --oneline <base>..`.

## After merge

1. **Stack:** if branches are stacked on the merged one, rebase them while its ref still exists. Update `<base>`, then run `git rebase --update-refs --onto <base> <merged> <top of stack>`. Set the upstream of the branch that sat directly on `<merged>` to `<base>`, push each rebased branch with `git push --force-with-lease`, and point that branch's PR at `<base>` with `gh pr edit --base`.
2. **Delete:** switch off the merged branch, then `git branch -d <branch>`. A squash-merged branch needs `-D`, once `gh pr view` shows it merged. Deleting writes `.git/config`, so run it outside any sandbox that blocks that file; otherwise the branch's config section stays behind.
