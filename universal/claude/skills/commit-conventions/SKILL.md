---
name: commit-conventions
description: >
  Use when creating git commits in any project. Covers mandatory commit body,
  Markdown formatting, staging discipline, the Write-tool + git-commit-F
  pattern for reliable commits, GPG signing in sandbox, and post-commit
  verification. This skill should be used whenever Claude is about to create
  a git commit, even if another commit-related skill or plugin is also
  active — this one provides the universal authoring rules. Triggers on:
  "commit", "git commit", "create a commit", "stage and commit", "fixup",
  "amend", "absorb", "autosquash", "reword".
---

# Commit Conventions

These rules apply to ALL projects. They layer on top of any project-level
or organization-level commit conventions (e.g., Jira ticket scoping, commit
type semantics, PR templates).

**Pick the path:**

- Creating a brand-new commit → follow **Writing → Staging → Creating** below.
- Amending code already on the current branch → jump to **§ Fixup Workflow**.
  Don't hand-craft fixup targets; use `git absorb`.
- Rewording a commit's message after rebase → **§ Post-Autosquash Message Review**.

## Writing the Commit Message

Format:
```
<type>(<scope>): <subject>

<body>

Co-Authored-By: Claude <model> <noreply@anthropic.com>
```

### Subject Line
- Max 72 characters
- Imperative mood ("add", not "added")
- No period at end

### Body (required, except for fixups)

Every commit needs a body explaining WHY the change was made — not just
restating what changed. A commit message without a body forces reviewers
to read the diff to understand intent, which slows down code review and
makes git history less useful.

- Wrap at 72 characters per line
- Use multiple paragraphs for longer explanations — group related ideas
- **Use Markdown formatting**: wrap code identifiers in backticks
  (function names, component names, prop names, file names, types)

**Exception:** Fixup commits created by `git absorb` or
`git commit --fixup=<sha>` are subject-only by design. Autosquash discards
fixup bodies, so the *why* lives in the squashed commit's body — verified
in the Post-Autosquash Message Review step.

**Example:**
```
feat(MIG-7922): add File Assessments table to application details

Add the `FileAssessmentsTable` component to the Application Details
page, backed by the `useFileAssessments` hook. The table shows
assessment results per file so users can see which files need attention
without navigating to a separate view.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

## Staging

Never use `git add .` or `git add -A`. Always stage specific files by
name: `git add path/to/file1 path/to/file2`.

When multiple agents work in parallel on the same worktree, `git add .`
can sweep up another agent's unstaged changes into your commit. Even in
solo work, it risks committing `.env` files, credentials, or other
unintended files. Explicit staging is always safer.

## Creating the Commit

Shell escaping is fragile for multi-line commit messages, especially
with backticks and special characters like `!` in `fixup!`. Use the
Write tool + `git commit -F` pattern instead:

1. Write the commit message to a unique file matching
   `/private/tmp/claude/commit-<id>.txt` using the Write tool
   (e.g. `commit-msg.txt`, `commit-fixup-upload.txt`). Use a
   descriptive `<id>` so parallel agents don't overwrite each other.
2. Run: `git -c commit.gpgsign=false commit -F /private/tmp/claude/commit-<id>.txt`

The `-c commit.gpgsign=false` flag prevents GPG/SSH signing hangs in
sandboxed environments where `ssh-agent` is not available.

## After Committing

Run `git status` to verify the commit succeeded and no unintended files
were included.

## Fixup Workflow

When amending code already on the current branch (relative to upstream),
use `git absorb` for target attribution. Don't hand-roll the
"which commit owns this hunk?" decision when blame-based attribution
already exists and is correct.

### Hard requirements

Both tools must be installed:

- **`git absorb`** — runs `git blame` on each staged hunk against commits
  in the current branch range and creates `fixup!` commits with the
  correct `--fixup=<sha>` target.
- **`git-branchless`** — used in the post-autosquash step (below) to
  reword commits without manual interactive rebase.

If either is missing, report it to the user and stop. Don't fall back
to a hand-rolled blame loop.

### Steps

1. **Stage the change.** Specific files only, per the staging rule above.
   **`git absorb` only inspects staged hunks** — anything you forget to
   stage is silently skipped. Run `git status` after staging to confirm
   nothing relevant is left out.
2. **Run `git absorb -v`.** Let absorb create `fixup!` commits with its
   own auto-generated bodies — don't pass `-m`.

   Skip `--dry-run`: `-v` already prints per-hunk attribution to stderr,
   and the resulting commits are trivially reversible with
   `git reset --soft HEAD~N`.
3. **Inspect the outcome.** Run `git log --oneline -10` to see what
   absorb created, and `git status` to see if any hunks were left
   unstaged because absorb couldn't attribute them.
4. **Handle leftovers.** For each leftover hunk or file, judge semantic
   fit using `git log --oneline <merge-base>..HEAD --stat`:

   | Situation | Action |
   |-----------|--------|
   | Clear single semantic match to a branch commit | Hand-author a fixup: `git -c commit.gpgsign=false commit --fixup=<sha>`. No message file — git auto-generates `fixup! <subject>` and ignores `-F`/`-m` with `--fixup`. The PostToolUse `verify-fixup-scope.py` hook runs as a file-scope safety net. |
   | Clearly net-new (new file, unrelated concern) | Normal commit using the standard rules above. |
   | Uncertain | Ask the user. Run `git log --oneline <merge-base>..HEAD` and present the candidate commits inline; don't default to a standalone commit. |

### Why no `-m` to `git absorb`

`-m` applies the same body to every fixup absorb generates. When absorb
produces multiple fixups (each targeting a different commit), each has
its own *why*, so a shared body is wrong. Letting absorb use its
auto-generated subject-only message is fine for fixups specifically —
autosquash discards the fixup body anyway. The semantic review of the
final squashed commit happens in the post-autosquash step.

## Post-Autosquash Message Review

After the user approves and runs `git rebase --autosquash <base>`, the
fixups are folded into their targets. Squashing in new code can make
the original commit's subject or body stale. Review every commit that
absorbed a fixup.

1. **Capture target subjects before rebase.** Run
   `git log --grep='^fixup!' --format='%s' <base>..HEAD` and strip the
   `fixup! ` prefix from each. Those subjects identify the commits to
   re-review post-rebase.
2. **After the rebase**, for each captured target subject, find the
   post-rebase commit with that subject — that's the squashed result
   to review.
3. **Review each one.** Run `git show <sha>`. For each:
   - Does the subject still describe what the commit does?
   - Does the body still cover the *why* of everything now in the
     diff (original work + absorbed fix)?
4. **Report — don't auto-reword.** Per-commit verdict:
   `still accurate` / `body should mention <X>` /
   `subject no longer describes the change`. The user decides whether
   to reword.

### Rewording on approval

When the user approves a reword:

1. Write the new full commit message to
   `/private/tmp/claude/reword-msg-<id>.txt` using the Write tool.
   Include subject, body, and `Co-Authored-By` trailer.
2. Run:
   ```
   GIT_EDITOR='cp /private/tmp/claude/reword-msg-<id>.txt' git branchless reword <sha>
   ```
   **Always spell out `git branchless reword`** — `git reword` may be
   aliased to `git stack reword` (a different tool), which would silently
   do the wrong thing. `git branchless reword` automatically rebases
   descendants onto the rewritten commit; no manual `git rebase -i`
   needed.
3. Verify: `git log --format=%B -n 1 <new-sha>` (the SHA changes — read
   it from the branchless output). If the message is empty, the `cp`
   path was wrong and git aborted; re-check the file path.
