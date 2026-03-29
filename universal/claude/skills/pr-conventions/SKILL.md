---
name: pr-conventions
description: >
  Write PR descriptions matching the user's preferred style. Use when
  creating a pull request, drafting a PR description, or when the user
  says "write a PR description", "create PR", "/pr-conventions".
  Layers on top of any project-level PR skills (e.g., edb-git-conventions:pr).
---

# PR Description Conventions

## Precedence

When both this skill and `edb-git-conventions:pr` are active, **this
skill's structure and tone take precedence**. Do NOT use the
What/Why/How/Test/Context template from `edb-git-conventions:pr`. Use
the narrative style and sections defined below instead.

## Research first

Before writing, read 2–3 of the user's recent merged PRs:

```bash
gh pr list --state merged --limit 5 --search "author:@me" --json number,title
gh pr view <number> --json body --jq '.body'
```

Style evolves — always check recent PRs for the latest conventions.

## Tone and structure

- **Conversational narrative**, not bullet-heavy structured templates.
  Write in first person ("I used", "I decided", "I also refactored").
- **Lead with what was added**, not why. The Jira ticket provides the
  why. The PR description explains the what and how.
- **Explain technical choices inline** in the narrative, not in a
  separate "Design Decisions" section. When a choice is non-obvious
  (e.g., XHR over fetch), explain it where it naturally comes up.
- **Keep it scannable.** Short paragraphs. No walls of text.

## Sections

Use these sections in order. Omit any section that has no content.

### Body (no heading)

The opening paragraphs — no `## Summary` heading. Just start
describing what the PR does.

For larger PRs, include subsections like `### Architecture` or
`### Component breakdown` when the implementation has enough
structure to warrant it. These are inline in the body, not
top-level sections.

### Test

`## Test` — what tests were added or run. Describe the coverage
briefly. Do **not** list exact test counts ("20 unit tests") —
describe the coverage areas ("unit tests for the upload manager
covering lifecycle, cancellation, and concurrency").

### Media

`## Media` — screenshots or video recordings. If you don't have
media yet, add an empty section with a TODO comment:

```markdown
## Media

<!-- TODO: Add video recording -->
```

### Known issues (optional)

`## Known issues` — only for genuine issues discovered during
implementation. Do **not** use this for planned future work.

### Future work (optional)

Use a heading like `## To implement in future chunks` or
`## Planned follow-ups` for work that is intentionally deferred.
List items briefly. This is distinct from known issues.

### References

`## References` — always present, always last. Include:
- Jira ticket link: `https://enterprisedb.atlassian.net/browse/TICKET-ID`
- Figma design link (if applicable)
- Related PRs (if applicable)

## What to avoid

- **No `## Summary` heading.** The body IS the summary.
- **No test count numbers.** Describe coverage, not counts.
- **No checklist-style test plans** (`- [ ] verify X`). Describe
  what the tests cover in prose.
- **No "Design Decisions" section.** Weave choices into the
  narrative.
- **No emoji.**
- **No `🤖 Generated with Claude Code` footer.** The co-author
  line in commits already attributes AI assistance.

## Example

```markdown
This PR adds the SQL file upload modal to the Migration Application
details page.

The modal has two steps: _Files_ (drag-and-drop file selection with
validation) and _Databases_ (target database version assignment per
file). On confirm, files are uploaded via XHR with concurrency control.

I used XHR instead of `fetch` because the Fetch API doesn't support
upload progress events — XHR's `upload.onprogress` is the only way
to get byte-level progress in the browser.

### Architecture

The upload infrastructure is built around an `UploadManager` class
that encapsulates a Zustand store, concurrency semaphore, and XHR
reference map for cancellation.

## Test

Unit tests for the upload manager covering lifecycle, cancellation,
auto-clear, and concurrency. Mocked Playwright E2E tests covering
the happy path, step navigation, file removal, error handling, and
search/sort.

## Media

<!-- TODO: Add video recording -->

## To implement in future chunks

- Progress header bar and upload details drawer
- Source database select and bulk target DB version assignment
- Live E2E tests against real backend

## References

- https://enterprisedb.atlassian.net/browse/MIG-7928
- [Figma design](https://www.figma.com/design/...)
```
