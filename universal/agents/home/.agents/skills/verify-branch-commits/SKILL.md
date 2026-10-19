---
name: verify-branch-commits
description: >
  Verify that every commit on the current branch passes all project checks
  independently. Use after rebasing, before creating a PR, or when picking
  up a branch. Triggers on: "verify commits", "verify branch", "check each
  commit", "per-commit verification", "/verify-branch-commits".
argument-hint: '[base-ref]'
---

# Verify Branch Commits

Step through every commit on the current branch and verify each one
passes the project's full check suite independently.

## Process

1. **Determine the base ref.** Use `$0` if provided, otherwise detect
   via `git merge-base HEAD main` (or `master`). Confirm with the user
   if uncertain.

2. **Discover the verification commands.** Read the project's
   `AGENTS.md`, `agent-docs/`, or `CLAUDE.md` for the specific
   commands covering compilation, linting, tests, and formatting.
   If not documented, ask the user.

3. **Start the verification rebase.** Mark every commit as `edit`:
   ```bash
   GIT_SEQUENCE_EDITOR="sed -i.bak 's/^pick /edit /g'" \
     git rebase -i <base-ref>
   ```

4. **At each stop**, run the full verification suite. If a check fails:
   - Fix the issue (e.g., format a file, fix a lint error).
   - Stage and amend: `git add <files> && git commit --amend --no-edit`
   - Note: amending may cause merge conflicts in later commits.
     Resolve them as they arise during `rebase --continue`.

5. **Check the commit message.** Verify that the commit message
   accurately reflects the current contents of the commit. After
   rebasing or amending, commit contents may have changed while the
   message stayed the same. If the message is stale or misleading:
   - Write the new message to `/tmp/agent-work/commit-reword.txt` using the agent's file-edit tool (create the scratch directory first)
   - Amend: `git commit --amend -F /tmp/agent-work/commit-reword.txt`
   - Note what was reworded for the final summary.

6. **Continue** to the next commit:
   ```bash
   git rebase --continue
   ```

7. **Repeat** steps 4–6 for every commit until the rebase completes.

8. **Report results.** Show the final `git log --oneline <base>..HEAD`
   and summarize any commits that needed fixing. If any commit
   messages were reworded, show the old → new message for each.

## Non-negotiables

- **Never skip a commit.** Every commit must be verified, even if
  "it's just a refactor" or "only touches tests."
- **Never skip a check.** Run all of: compilation, linting, tests,
  and formatting. A commit that passes lint but fails compilation is
  not acceptable.
- **Fix, don't skip.** If a commit fails, fix it and amend. Do not
  mark it as "known failure" and move on.
- **No pre-existing failures.** Do not assume any test or check
  failure is pre-existing. Everything passes on `main`, and
  everything must pass on every branch commit.

## Example output

```
Verifying 6 commits on proj-789/csv-import-chunk-1 (base: main)

  ✓ a1b2c3d refactor(PROJ-789): extract CSV parsing and query options
  ✓ b2c3d4e refactor(PROJ-789): export API request helpers
  ⚠ c3d4e5f chore(PROJ-789): add CSV import utilities and store
    → prettier: 2 files reformatted, amended
  ✓ d4e5f6a feat(PROJ-789): add CSV import modal
  ✓ e5f6a7b feat(PROJ-789): wire import modal into details page
    → reworded: "feat(PROJ-789): add import button to details page"
      → "feat(PROJ-789): wire import modal into details page"
  ✓ f6a7b8c test(PROJ-789): add import flow E2E tests

All 6 commits pass verification.
```
