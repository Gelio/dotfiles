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
  "amend".
---

# Commit Conventions

These rules apply to ALL projects. They layer on top of any project-level
or organization-level commit conventions (e.g., Jira ticket scoping, commit
type semantics, PR templates).

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

### Body (always required)

Every commit needs a body explaining WHY the change was made — not just
restating what changed. A commit message without a body forces reviewers
to read the diff to understand intent, which slows down code review and
makes git history less useful.

- Wrap at 72 characters per line
- Use multiple paragraphs for longer explanations — group related ideas
- **Use Markdown formatting**: wrap code identifiers in backticks
  (function names, component names, prop names, file names, types)

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

1. Write the commit message to `/private/tmp/claude/commit-msg.txt`
   using the Write tool
2. Run: `git -c commit.gpgsign=false commit -F /private/tmp/claude/commit-msg.txt`

The `-c commit.gpgsign=false` flag prevents GPG/SSH signing hangs in
sandboxed environments where `ssh-agent` is not available.

### Fixup Commits

Same pattern, but prefix the subject with `fixup! `:

```
fixup! feat(MIG-7922): add File Assessments table

Fix missing null check in `FileAssessmentsTable` when the API returns
an empty response.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

## After Committing

Run `git status` to verify the commit succeeded and no unintended files
were included.
