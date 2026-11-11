---
name: session-handoff
description: Write a permanent handoff for the next session and refresh the workstream's tracker.
disable-model-invocation: true
argument-hint: "[workstream]"
---

# Session handoff

Read [`REFERENCE.md`](REFERENCE.md) first: it defines workstreams, trackers and handoffs, their paths, lookups and formats.

## Steps

1. **Workstream.** Use the argument if given. Otherwise list the workstreams and match this session's work to one. When several active ones could fit, ask the user which. New work gets a new kebab-case name.
2. **Previous.** The newest handoff of the workstream is `previous`; no match means `none`.
3. **State.** Run the State commands now. Every State field comes from their output.
4. **ADR.** Mark each decision that governs the whole repo `ADR candidate` in Decided, and invoke `domain-modeling` to decide whether to offer the ADR.
5. **Write** the handoff, taking the timestamp from `date '+%Y-%m-%d %H:%M'` and using a few kebab-case words for the slug. If the name is taken, choose another slug.
6. **Tracker.** Create or rewrite it: fold in this session's decisions and gotchas, remove what they supersede, and link the new handoff. A workstream with a chain but no tracker gets one built from its newest handoff. On creation, link the external tracker this session already references, or ask the user whether one exists. Set Status to `done` when the user confirms the goal is met.
7. **External tracker.** If one is linked, draft a short progress comment and post it only after the user approves it.
8. **Print** one line for the user to paste into a fresh session, as your last output:
   `/session-pickup <workstream>`
