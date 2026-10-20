---
name: todos
description: Work through a todos.md task list with subagent delegation, TODO tracking, and commit strategy. Use when the user says "work on todos", "pick up todos", "/todos <path>", "work through the remaining tasks", or references a todos.md file they want worked through. Also use when a user says "pick up where you left off" and a todos.md exists in the working directory. Triggers on any mention of working through a checklist file or task list file.
---

# Working Through todos.md Files

You are the orchestrator. You read the task list, delegate code changes to subagents, track progress, and manage commits.

## Non-negotiables

1. **Delegate code changes when subagents are available and authorized.**
   Otherwise work through the tasks directly; keep the same verification and
   tracking workflow.
2. **Rebase yourself only when the whole range is unpushed.** Unpushed is defined in `commit-conventions` § Unpushed History. If every commit in the rebase range is unpushed, run the rebase after the last task (§ Rebase). Otherwise present the commit plan and rebase only after the user approves it.
3. **Use the `commit-conventions` skill** for every commit. It handles message format, staging, and the Write-tool + `git commit -F` pattern.
4. **Mark tasks done immediately.** Edit the selected TODO file to change `- [ ]` to `- [x]` right after each task completes — do not batch.

## Startup

1. Read the file at the selected TODO file. If not provided, look for a `todos.md` in the current directory or ask the user.
2. Parse all `- [ ]` items.
3. Skip items under headings that fuzzy-match these patterns (match loosely — "Stuff I'll handle myself" counts as "For me"):
   - "For me" / "My tasks" / "Things for me to do"
   - "For later" / "Later" / "Deferred"
   - "Known issues" / "Known problems"
   - "Won't fix" / "Out of scope"
4. Treat the selected TODO file as the source of truth. Mirror actionable
   items into the agent's native task tracker when one is available.

## Working Through Tasks

Process tasks in order, top to bottom. For each task:

1. Read the task description. Gather context (file paths, conventions, references) needed for a clear subagent brief.
2. If delegating, brief the subagent with:
   - What to change and why
   - Relevant file paths
   - Conventions or patterns to follow
   - Expected result
3. Verify the result, whether implemented directly or by a subagent.
4. Mark `- [x]` in the selected TODO file and update any native task entry.
5. Report briefly, then move on.

Run independent tasks (no overlapping files) in parallel via concurrent subagents.

## Commit Strategy

Use `/commit-conventions` for the mechanics. These rules govern **when** and **what kind**:

| Condition | Action |
|-----------|--------|
| Task mentions a new/separate/standalone commit (e.g., **new commit**, "separate commit", "own commit") | New standalone commit |
| Change fixes code introduced by a commit in `<merge-base>..HEAD` (i.e., still on this branch, not yet merged) | Follow the fixup workflow in `/commit-conventions` (uses `git absorb`) |
| Uncertain | Standalone commit, flagged in the completion summary with its candidate targets (see `/commit-conventions` § Fixup Workflow). |

While working through tasks, create new commits (standalone or fixup) rather than amending, so each task's change stays separately visible until the rebase.

### Fixup attribution

For fixup commits, follow the workflow in `/commit-conventions`. It covers
target attribution via `git absorb`, the semantic-fallback path for hunks
absorb can't attribute, and how to handle hunks with an uncertain target.

A shared fixup-scope check, registered by each agent's PostToolUse adapter, runs as an
advisory file-scope safety net. Absorb-created fixups are file-scope-correct
by construction and won't trip it; warnings come from the hand-authored
fallback path. Heed those warnings unless the extra files are genuinely
required by the fix.

### Commit ordering

Think about the final commit order while you work. Each commit should only depend on code introduced by commits **before** it, not after. If a new standalone commit introduces something that an earlier commit will rely on, that new commit needs to be reordered earlier during the rebase. Plan for this — note the intended final order in the completion summary so the rebase gets it right.

### Example flow

Given a todos.md task: `- [ ] Fix null check in InvoicesTable`

1. You check `git log --oneline main..HEAD` and see `abc1234 feat(PROJ-456): add Invoices table`
2. You spawn a subagent: "Fix the null check in `InvoicesTable` when the API returns an empty response. File: `web/src/pages/.../InvoicesTable.tsx`"
3. Subagent completes the fix
4. You stage the file and run `git absorb`. Absorb attributes the hunk
   to `abc1234` and creates `fixup! feat(PROJ-456): add Invoices table`.
5. You check `git log --oneline -5` and `git status` to confirm: one fixup
   commit created, nothing left unstaged.
6. You mark `- [x]` in the todos.md and report: "Fixed null check — `git absorb` created a fixup for `abc1234`."

## Completion Summary

When done (or blocked), provide:

1. Completed tasks — what was done for each.
2. Skipped tasks — which heading matched and why.
3. Remaining tasks — blockers or reasons.
4. **Current commit history** (as-is on the branch):
   ```
   Current commits (in creation order):
   - abc1234 feat(PROJ-456): add Invoices table
   - def5678 fixup! feat(PROJ-456): add Invoices table  (null check)
   - ghi9012 feat(PROJ-456): add shared utility for invoices
   - jkl3456 feat(PROJ-456): add bar styling
   ```
5. **Planned final order** after rebase (with reordering and fixup squashing):
   ```
   Planned final order:
   1. feat(PROJ-456): add shared utility for invoices   ← moved earlier (bar styling depends on it)
   2. feat(PROJ-456): add Invoices table                ← includes fixup (null check)
   3. feat(PROJ-456): add bar styling
   ```
6. **Rebase status:**
   - Whole range unpushed → run § Rebase now, then report the final
     `git log --oneline`, the backup ref name, and any rewords.
   - Otherwise ask: **"Do you want me to proceed with the rebase, or do you need more changes first?"**

## Rebase

Run on your own when the whole range is unpushed; otherwise only after the user approves.

1. Save the backup ref from `commit-conventions` § Unpushed History. If the
   rebase hits a conflict you can't resolve with certainty, run
   `git rebase --abort` and hand the plan to the user instead.
2. Run `git rebase --autosquash -i <base-commit>` using `GIT_SEQUENCE_EDITOR` to apply the planned order non-interactively. The sequence editor script must reorder picks to match the planned final order and let `--autosquash` handle fixup placement.
3. If there are no reordering needs (only fixups to squash), a plain `git rebase --autosquash <base-commit>` suffices.
4. After the rebase, run the project's checks on the final `HEAD` and show the final `git log --oneline` so the user can verify.
5. Run the **post-autosquash message review** from the `commit-conventions` skill —
   for each commit that absorbed a fixup, verify the subject and body still
   describe what the commit now does, and reword per that skill.
6. Signing reminder with the actual base commit SHA:
   > Remember to sign the commits before pushing: `git rebase --gpg-sign <base-commit>`
