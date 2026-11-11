---
name: session-handoff
description: Write a permanent handoff file for the next session, and refresh the workstream's tracker if it has one.
disable-model-invocation: true
argument-hint: "[workstream]"
---

# Handoff

A **handoff** is a permanent file that lets a fresh session continue the work. It holds only what git cannot show, and points to commits and files instead of copying diffs. The handoffs of one **workstream** form a **chain** through their `previous` field. A **tracker** holds a workstream's mutable current state.

Paths are relative to the repo root.

## Steps

1. **Workstream.** Use the argument if given. Otherwise list the existing ones with `grep -h '^workstream: ' .claude/handoffs/*.md | sort -u` and match this session's work to one. When several active workstreams could fit, ask the user which. New work gets a new kebab-case name.
2. **Previous.** `grep -lx 'workstream: <name>' .claude/handoffs/*.md | sort | tail -1` finds the newest handoff in the chain. Its filename is `previous`; no match means `none`.
3. **State.** Run these now, for the branch holding the workstream's work, which may differ from the one checked out. Every State field comes from this output:
   - Branch and upstream: `git for-each-ref --format='%(refname:short) %(upstream:short) %(upstream:track)' refs/heads/<branch>`
   - Commit: `git log -1 --format='%h %s' <branch>`
   - Pushed: `git ls-remote origin <branch>`. Empty means not pushed; a different SHA means the remote differs from local.
   - Merged: `git merge-base --is-ancestor <commit> origin/<default branch>`, after `git fetch origin`.
   - Uncommitted: `git status --short`.
4. **ADR.** Mark each decision that governs the whole repo `ADR candidate` in Decisions, and invoke `domain-modeling` to decide whether to offer the ADR.
5. **Write** `.claude/handoffs/YYYY-MM-DD-HHMM-<slug>.md` in the format below, taking the timestamp from `date '+%Y-%m-%d %H:%M'` and using a few kebab-case words for the slug. If the name is taken, choose another slug.
6. **Tracker.** If `.claude/tracking/<workstream>.md` exists, rewrite it now and link the new handoff. Create a tracker only when the user asks for one.
7. **Print** one line for the user to paste into a fresh session, as your last output:
   `Read .claude/handoffs/<file>, re-check its State, then do its Next action.`

## Handoff format

About 40 lines at most. Write `None` under a section with nothing to record.

````markdown
---
date: YYYY-MM-DD HH:MM
workstream: <name>
previous: <filename of the previous handoff in this workstream, or none>
---

> Re-check State with git before trusting this file. Where they disagree, git is right and this file is stale.

## Goal

## State

Branch, commit, pushed or not, merged or not, uncommitted work.

## Verified vs unverified

Which command proved what, then what nobody has checked.

## Decisions

Chosen, rejected, why. Link the earlier handoff when this supersedes its decision.

## Gotchas

## Next action

One concrete first step.
````

Handoffs are permanent and immutable. Correct one by writing a new handoff that links to it, and leave every existing file in place, unchanged. Whether they are gitignored is the repo's call; keep its ignore rules as they are.

## Tracker format

One file per long-running workstream at `.claude/tracking/<workstream>.md`, rewritten in place. It holds the present only; history lives in the chain.

```markdown
# <workstream>

**Status:** where things stand, in a line or two.

## Open items

## Blockers

## Latest handoff

[<filename>](../handoffs/<filename>)
```
