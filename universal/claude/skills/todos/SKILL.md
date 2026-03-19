---
name: todos
description: Work through a todos.md task list with subagent delegation, TODO tracking, and commit strategy. Use when the user says "work on todos", "pick up todos", "/todos <path>", "work through the remaining tasks", or references a todos.md file they want worked through. Also use when a user says "pick up where you left off" and a todos.md exists in the working directory. Triggers on any mention of working through a checklist file or task list file.
argument-hint: '<path-to-todos.md>'
---

# Working Through todos.md Files

You are the orchestrator. You read the task list, delegate code changes to subagents, track progress, and manage commits.

## Non-negotiables

1. **Delegate all code changes to subagents.** Do not write code yourself. Your context is for orchestration — subagents are disposable and keep your window clean for managing remaining tasks.
2. **Do not rebase until the user explicitly approves.** Present the commit plan first. Only run the rebase after the user confirms they don't need more changes.
3. **Use `/commit-conventions`** for every commit. It handles message format, staging, and the Write-tool + `git commit -F` pattern.
4. **Mark tasks done immediately.** Edit `$0` to change `- [ ]` to `- [x]` right after each task completes — do not batch.

## Startup

1. Read the file at `$0`. If not provided, look for a `todos.md` in the current directory or ask the user.
2. Parse all `- [ ]` items.
3. Skip items under headings that fuzzy-match these patterns (match loosely — "Stuff I'll handle myself" counts as "For me"):
   - "For me" / "My tasks" / "Things for me to do"
   - "For later" / "Later" / "Deferred"
   - "Known issues" / "Known problems"
   - "Won't fix" / "Out of scope"
4. Create a Claude Code TODO entry for each actionable unchecked item.

## Working Through Tasks

Process tasks in order, top to bottom. For each task:

1. Read the task description. Gather context (file paths, conventions, references) needed for a clear subagent brief.
2. Spawn a subagent with:
   - What to change and why
   - Relevant file paths
   - Conventions or patterns to follow
   - Expected result
3. Verify the subagent's result.
4. Mark `- [x]` in `$0` and update the TODO entry.
5. Report briefly, then move on.

Run independent tasks (no overlapping files) in parallel via concurrent subagents.

## Commit Strategy

Use `/commit-conventions` for the mechanics. These rules govern **when** and **what kind**:

| Condition | Action |
|-----------|--------|
| Task mentions a new/separate/standalone commit (e.g., **new commit**, "separate commit", "own commit") | New standalone commit |
| Change fixes code from a recent branch commit | `fixup!` commit targeting that commit's subject |
| Uncertain | Normal standalone commit |

Never amend commits — always create new ones (standalone or fixup). The user reviews the full commit list before any squashing.

### Commit ordering

Think about the final commit order while you work. Each commit should only depend on code introduced by commits **before** it, not after. If a new standalone commit introduces something that an earlier commit will rely on, that new commit needs to be reordered earlier during the rebase. Plan for this — note the intended final order in the completion summary so the rebase gets it right.

### Example flow

Given a todos.md task: `- [ ] Fix null check in FileAssessmentsTable`

1. You check `git log --oneline main..HEAD` and see `abc1234 feat(MIG-7922): add File Assessments table`
2. You spawn a subagent: "Fix the null check in `FileAssessmentsTable` when the API returns an empty response. File: `onprem/ui/src/pages/.../FileAssessmentsTable.tsx`"
3. Subagent completes the fix
4. You create a fixup commit via `/commit-conventions`:
   ```
   fixup! feat(MIG-7922): add File Assessments table

   Fix missing null check in `FileAssessmentsTable` when the API
   returns an empty `items` array.
   ```
5. You mark `- [x]` in the todos.md and report: "Fixed null check — created fixup commit for abc1234"

## Completion Summary

When done (or blocked), provide:

1. Completed tasks — what was done for each.
2. Skipped tasks — which heading matched and why.
3. Remaining tasks — blockers or reasons.
4. **Current commit history** (as-is on the branch):
   ```
   Current commits (in creation order):
   - abc1234 feat(MIG-7922): add File Assessments table
   - def5678 fixup! feat(MIG-7922): add File Assessments table  (null check)
   - ghi9012 feat(MIG-7922): add shared utility for assessments
   - jkl3456 feat(MIG-7922): add bar styling
   ```
5. **Planned final order** after rebase (with reordering and fixup squashing):
   ```
   Planned final order:
   1. feat(MIG-7922): add shared utility for assessments   ← moved earlier (bar styling depends on it)
   2. feat(MIG-7922): add File Assessments table            ← includes fixup (null check)
   3. feat(MIG-7922): add bar styling
   ```
6. Ask: **"Do you want me to proceed with the rebase, or do you need more changes first?"**

## Rebase

Only after the user explicitly approves — do not proceed on your own.

1. Run `git rebase --autosquash -i <base-commit>` using `GIT_SEQUENCE_EDITOR` to apply the planned order non-interactively. The sequence editor script must reorder picks to match the planned final order and let `--autosquash` handle fixup placement.
2. If there are no reordering needs (only fixups to squash), a plain `git rebase --autosquash <base-commit>` suffices.
3. After the rebase, show the final `git log --oneline` so the user can verify.
4. Signing reminder with the actual base commit SHA:
   > Remember to sign the commits before pushing: `git rebase --gpg-sign <base-commit>`
