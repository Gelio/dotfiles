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
   via `git merge-base HEAD <default>`, where `<default>` comes from
   `git symbolic-ref --short refs/remotes/origin/HEAD`, else whichever
   of `main` / `master` exists. State the base you picked and proceed;
   ask only when both `main` and `master` exist or neither does.

2. **Discover the verification commands.** Read the project's
   `AGENTS.md`, `agent-docs/`, or `CLAUDE.md` for the specific
   commands covering compilation, linting, tests, and formatting.
   If not documented, derive them from the CI workflow, `package.json`
   scripts, `Makefile`, or equivalent, and list the commands you chose
   in the report. Ask the user only when none of these exist.

3. **Check the range is unpushed.** This process amends commits, so run
   the check from `commit-conventions` § Unpushed History on
   `<base>..HEAD` and save its backup ref. If any commit is already
   pushed, run the checks without amending (`git rebase -x '<checks>'
   <base>`, stopping at failures) and report the fixes for the user to
   approve.

4. **Start the verification rebase.** Mark every commit as `edit`:
   ```bash
   GIT_SEQUENCE_EDITOR="sed -i.bak 's/^pick /edit /g'" \
     git rebase -i <base-ref>
   ```

5. **At each stop**, run the full verification suite. If a check fails:
   - Fix the issue (e.g., format a file, fix a lint error).
   - Stage and amend: `git add <files> && git commit --amend --no-edit`
   - Note: amending may cause merge conflicts in later commits.
     Resolve them as they arise during `rebase --continue`.

6. **Check the commit message.** Verify that the commit message
   accurately reflects the current contents of the commit. After
   rebasing or amending, commit contents may have changed while the
   message stayed the same. If the message is stale or misleading:
   - Write the new message to `/tmp/agent-work/commit-reword.txt` using the agent's file-edit tool (create the scratch directory first)
   - Amend: `git commit --amend -F /tmp/agent-work/commit-reword.txt`
   - Note what was reworded for the final summary.

7. **Continue** to the next commit:
   ```bash
   git rebase --continue
   ```

8. **Repeat** steps 5–7 for every commit until the rebase completes.

9. **Report results.** Show the final `git log --oneline <base>..HEAD`
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
