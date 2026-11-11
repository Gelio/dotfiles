# Session handoffs: reference

Shared by `/session-handoff`, which writes these files, and `/session-pickup`, which reads them.

## Terms

- A **workstream** is one line of work, named in kebab-case, that spans sessions.
- A **tracker** holds a workstream's current truth: status, decisions in force, gotchas. It is rewritten in place, so it never holds history.
- A **handoff** is what one session adds: what it did, what it verified, what is in flight, the next action. Handoffs are permanent and immutable. The handoffs of one workstream form a **chain** through their `previous` field, which is the workstream's history.
- An **external tracker** is a GitHub issue or Linear issue that people follow. When a tracker links one, the external tracker owns status and open items, and the local tracker leaves them out instead of copying them.

## Paths

Paths are relative to the main worktree's root, `dirname "$(git rev-parse --path-format=absolute --git-common-dir)"`, so sessions in every worktree share one set of files.

- Trackers: `.claude/tracking/<workstream>.md`
- Handoffs: `.claude/handoffs/YYYY-MM-DD-HHMM-<slug>.md`

Whether these are gitignored is the repo's call; keep its ignore rules as they are.

## Lookups

- Workstreams and their status: `grep -H '^\*\*Status:\*\*' .claude/tracking/*.md`. A status starting with `done` closes the workstream.
- Workstreams that have handoffs but no tracker predate trackers: `grep -h '^workstream: ' .claude/handoffs/*.md | sort -u`, minus the tracked ones.
- Newest handoff of a workstream: `grep -lx 'workstream: <name>' .claude/handoffs/*.md | sort | tail -1`.

## State commands

Run these for the branch holding the workstream's work, which may differ from the one checked out. Run `git status` in the worktree that has that branch checked out (`git worktree list`).

- Branch and upstream: `git for-each-ref --format='%(refname:short) %(upstream:short) %(upstream:track)' refs/heads/<branch>`
- Commit: `git log -1 --format='%h %s' <branch>`
- Pushed: `git ls-remote origin <branch>`. Empty means not pushed; a different SHA means the remote differs from local.
- Merged: `git merge-base --is-ancestor <commit> origin/<default branch>`, after `git fetch origin`.
- Uncommitted: `git status --short`.

## Tracker format

```markdown
# <workstream>

**Status:** active or done, then where things stand in a line or two.
**External tracker:** <issue URL, or none>

## Goal

## Open items

Only without an external tracker.

## Decisions

Each decision in force, with a one-line why. Remove a superseded one; the handoff that superseded it keeps the reason.

## Gotchas

Traps and failed approaches still worth avoiding.

## Latest handoff

[<filename>](../handoffs/<filename>)
```

## Handoff format

About 25 lines at most. It holds only what git cannot show, and points to commits and files instead of copying diffs. Write `None` under a section with nothing to record.

````markdown
---
date: YYYY-MM-DD HH:MM
workstream: <name>
previous: <filename of the previous handoff in this workstream, or none>
---

> Re-check State with git before trusting this file. Where they disagree, git is right and this file is stale.

## Done

What this session changed, by commit.

## State

Branch, commit, pushed or not, merged or not, uncommitted work.

## Verified vs unverified

Which command proved what, then what nobody has checked.

## In flight

Half-done work, stashes, hypotheses being tested.

## Decided

Decisions made this session, one line each. The tracker holds the full set in force.

## Open questions

For the user.

## Next action

One concrete first step, and the files to read before it.
````

Correct a handoff by writing a new one that links to it, and leave every existing handoff in place, unchanged.
