---
name: commit-conventions
description: >
  Use when creating git commits in any project. Covers mandatory commit body,
  Markdown formatting, staging discipline, the Write-tool + git-commit-F
  pattern for reliable commits, and post-commit
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

#### What belongs in the body

The body's job is to give a reviewer what the diff can't: the constraint
that motivated the change, the alternatives that were rejected, and the
non-obvious decisions baked into the chosen approach.

**Do** include:

- The external constraint or fact that forced this change ("GHA only
  propagates secrets through `uses:` + `secrets: inherit`, not through
  `workflow_dispatch`")
- Why this approach was chosen over alternatives ("`strings.Contains`
  rather than an enum because future Oracle scenarios should be covered
  automatically")
- What the change deliberately does NOT do, and why ("no
  `BEACON_AGENT_VERSION` input — auto-alignment tracked by MIG-7276")
- Cross-references to related sites the reader should know about ("the
  `oracleImage()` TODO cross-references this CI guard")

**Don't** restate things the diff already shows:

- Identifiers, strings, or values quoted from the diff. If the change
  adds `slog.String("reason", "X")`, don't add a paragraph that quotes
  `"X"` back — the reader sees it.
- File-structure inventories ("the README has three sections: 1... 2...
  3..."). The reader can open the file.
- Mechanical plumbing inside a step (`set -euo pipefail`, exit-status
  branching, the exact `kubectl` invocations) when only the *existence
  and purpose* of the step is the load-bearing fact.
- Justifications for stylistic choices the reader wouldn't otherwise
  question ("multi-line `|` description so the GitHub UI has room") —
  defending a routine formatting choice draws attention rather than
  deflecting it.

**Don't** reference things the reader can't see:

The commit body's audience is "a future engineer reading `git log`,"
not "the agent / human at the moment of authoring." References that
only resolve in the authoring session are noise to that audience.

- **Gitignored or out-of-repo artifacts** (`agent-plans/...`, scratch
  notes, decisions ledgers, working-tree-only files, `pr-description-notes.md`).
  Anyone reading the commit can't `cat` them. If the *fact* they capture
  is load-bearing for the commit, inline the fact instead. If it isn't,
  drop the reference.
- **Plan-internal labels** like `PR-BS1`, `Q13`, `Task 17`, `Phase 3
  milestone`, `the cleanup commit per the lifecycle`. Those names exist
  in the agent's own progress tracking; in a commit body they read as
  jargon to the reader, who has no way to resolve them. Refer to things
  that ARE in the repo or git history: file paths, commit SHAs, ticket
  keys, ref/branch names, PR numbers (once known).
- **Cross-PR coordination narrative** ("merge minutes before X",
  "do this last per the race window"). The reasoning is real, but it
  belongs in the PR description / merge-queue comment, not in a commit
  body that outlives both.

If the change has external proof that helps a reviewer trust it (CI
run URLs, a passing dispatch, a reproduced bug log), link to it
directly in the body — those *are* reachable to a future reader.

Rule of thumb: if a sentence would still be true word-for-word *without
this commit*, or if it just narrates the diff, cut it.

#### Formatting

- Wrap at 72 characters per line
- Use multiple paragraphs for longer explanations — group related ideas
- For enumerations of 3+ items, prefer a bulleted list over a
  parenthetical or semicolon-separated inline list — easier to scan,
  easier to extend in a later commit
- Name the specific owner of a resource rather than a generic category
  (write "`edbpgai-bootstrap` repository secrets", not "org secrets" —
  if the reader needs to grant or rotate the secret, the generic noun
  doesn't tell them where to go)
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
2. Run: `git commit -F /private/tmp/claude/commit-<id>.txt`

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
2. **Run `git absorb`.** Let absorb create `fixup!` commits with its
   own auto-generated bodies — don't pass `-m`.

   Skip `--dry-run`: the resulting commits are trivially reversible with
   `git reset --soft HEAD~N`, and step 3 inspects the outcome via
   `git log` / `git status` anyway.
3. **Inspect the outcome.** Run `git log --oneline -10` to see what
   absorb created, and `git status` to see if any hunks were left
   unstaged because absorb couldn't attribute them.
4. **Handle leftovers.** For each leftover hunk or file, judge semantic
   fit using `git log --oneline <merge-base>..HEAD --stat`:

   | Situation | Action |
   |-----------|--------|
   | Clear single semantic match to a branch commit | Hand-author a fixup: `git commit --fixup=<sha>`. No message file — git auto-generates `fixup! <subject>` and ignores `-F`/`-m` with `--fixup`. The PostToolUse `verify-fixup-scope.py` hook runs as a file-scope safety net. |
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
