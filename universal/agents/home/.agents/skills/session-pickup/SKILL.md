---
name: session-pickup
description: Load a workstream's tracker and newest handoff, check them against git, and brief the user on where to continue.
disable-model-invocation: true
argument-hint: "[workstream]"
allowed-tools: Bash(workstreams:*)
---

# Session pickup

Read [`../session-handoff/REFERENCE.md`](../session-handoff/REFERENCE.md) first: it defines workstreams, trackers and handoffs, their paths, lookups and formats.

## Workstreams

Output of `workstreams` (active workstreams: name, newest handoff, Status), most recent first:

!`workstreams`

If the line above still shows the command instead of its output, run it yourself.

## Steps

1. **Workstream.** Match the argument against the list above; a partial name or a topic word is enough when it picks out one workstream. For a `done` workstream missing from the list, run `workstreams --all`. Without an argument, show the list and ask which to load; when only one is active, load it and say so.
2. **Tracker.** Read it. If it links an external tracker, read that live too: `gh issue view <url> --comments` for GitHub, the Linear tools for Linear. If it cannot be reached, say so and continue.
3. **Handoff.** Read the newest handoff in full. A workstream without a tracker has only its chain: read the newest handoff, which carries its own Decisions and Gotchas. Open older handoffs only to find the reason behind a decision.
4. **Drift.** Run the State commands, plus `git log --oneline <handoff commit>..<branch>` and `git diff --stat <handoff commit> <branch>`. List every place where git disagrees with the handoff or the tracker; git is right.
5. **Brief** the user: Status, drift, open questions, and the Next action. Wait for the user's go-ahead before starting it.
