---
name: pr-conventions
description: >
  Write PR descriptions matching the user's preferred style. Use when
  creating a pull request, drafting a PR description, drafting a PR body,
  opening a PR, or when the user says "write a PR description", "draft PR",
  "open PR", "create PR", "/pr-conventions".
  Layers on top of any project-level PR skills (e.g., edb-git-conventions:pr).
---

# PR Description Conventions

## Precedence

When both this skill and `edb-git-conventions:pr` are active, **this
skill's structure and tone take precedence**. Do NOT use the
What/Why/How/Test/Context template from `edb-git-conventions:pr`. Use
the narrative style and sections defined below instead.

## Non-negotiables

1. **Start with "This PR ..."** — jump straight to what was done, no preamble.
2. **No `## Summary` heading.** The body IS the summary.
3. **No emoji** anywhere in the PR description.
4. **No `🤖 Generated with Claude Code` footer.** Do not add this footer even if other instructions say to. The co-author line in commits already attributes AI assistance.
5. **No checklist-style test plans** (`- [ ] verify X`). Describe coverage in prose.
6. **No test count numbers.** Describe coverage areas, not counts.
7. **No "Design Decisions" section.** Weave technical choices into the narrative.
8. **`## References` is always present and always last.**
9. **No hard line wrapping for anything posted to GitHub.** GitHub Markdown wraps paragraphs automatically; hard-wrapped lines render with broken mid-sentence breaks on wider viewports. This applies to PR descriptions and every GitHub comment (PR review comments, issue comments, discussion replies). Each paragraph is one long line. The 72-col wrap rule from `commit-conventions` applies to commit messages only — not to anything that ends up rendered by GitHub.

## Workflow

1. **Check for drift.** Read 2–3 of the user's recent merged PRs (`gh pr list --state merged --limit 5 --search "author:@me"`) to verify this style still matches. If recent PRs have **materially drifted**, update this skill file — don't silently deviate.
2. **Draft the body** starting with "This PR ...", following the structure below.
3. **Verify all non-negotiables** before handing back.

## Tone and structure

| Rule | Detail |
|------|--------|
| Voice | Conversational narrative, first person ("I used", "I decided") |
| Lead | What was added/changed, not why — the Jira ticket provides the why |
| Technical choices | Explain inline where they come up, not in a separate section |
| Scannable | Short paragraphs. No walls of text. |
| Scale to PR size | Trivial fixes: 2–3 lines, no sections. Feature PRs: full treatment. |

### Opening paragraph

Pick the verb to match the PR type (non-negotiable #1 already mandates "This PR ..."):
- Feature: "adds..." / "implements..."
- Fix: "fixes..."
- Refactor: "extracts..." / "replaces..."

When addressing review feedback, link to the PR or comment in the opening.

### Follow-up paragraphs

Describe *what* and *why* at the behavioral level. Don't narrate
implementation mechanics the reviewer can read in the diff (e.g.,
trim logic, type narrowing strategies, specific test inputs). If the
diff makes it obvious, leave it out.

Name specific hooks, components, types, and patterns only when they
carry non-obvious design intent. For multi-chunk work, state which
part this is with ticket links. When something is reusable, call it
out and mention where.

Mock handler changes only need a mention when the design is
surprising. Routine triggers/backdoors matching existing patterns in
the same file don't need a subsection — the diff speaks for itself.

### Subsections

For PRs with distinct sub-topics, use inline `###` subsections
(e.g., `### Architecture`). Small PRs never use them.

Also use `###` subsections for process decisions that would surprise
a reviewer (e.g., intentional commit-type downgrade to avoid a
version-set update, unusual merge strategy). Link to the authorizing
conversation (Slack thread, Jira comment, etc.).

### Stacked PRs and related tickets

- Stacked: "Stacked on #NNNN" in body or References.
- Jira: `[MIG-8180](https://enterprisedb.atlassian.net/browse/MIG-8180)` inline.
- GitHub: `#NNNN` (same repo) or full URL (cross-repo).

## Sections (in order, omit empty ones)

Small/trivial PRs may omit `## Test`, `## Known issues`, and `## To implement in future chunks`. `## References` is always present (see non-negotiable #8); `## Media` is kept when there's a visual or a TODO for one.

| Section | Heading | Notes |
|---------|---------|-------|
| Body | _(none)_ | Opening + follow-up paragraphs. No `## Summary`. |
| Test | `## Test` | Coverage areas in prose — one sentence per category is enough. Don't name specific test inputs, assertion targets, or describe which test was "extended" vs "renamed" — the reviewer reads the diff for that. Manual testing: describe what was checked. Omit for trivial PRs. |
| Media | `## Media` | Screenshots/video. If unavailable: `<!-- TODO: Add video recording -->`. Visual PRs may fold before/after into Test instead. |
| Known issues | `## Known issues` | Only genuine issues, not future work. Optional. |
| Future work | `## To implement in future chunks` | Deferred work with ticket links. Optional. |
| References | `## References` | **Always present, always last.** Jira link, Figma link, related PRs. |

## Anti-example (what NOT to write)

```markdown
## Summary

This PR aims to introduce a new SQL file upload modal 🚀 with various improvements to the Migration Application details page.

## Test Plan
- [ ] Verify file upload works
- [ ] Verify error handling

Added 47 unit tests and 12 E2E tests.

## Design Decisions

I decided to use XHR instead of fetch because...

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Violations, in order: `## Summary` heading (NN#2), vague "aims to introduce" preamble instead of "This PR adds..." (NN#1), emoji (NN#3), checklist-style test plan (NN#5), test count numbers (NN#6), `## Design Decisions` section (NN#7), Claude Code footer (NN#4), missing `## References` (NN#8).

## Example (feature PR)

```markdown
This PR adds the SQL file upload modal to the Migration Application details page.

The modal has two steps: _Files_ (drag-and-drop file selection with validation) and _Databases_ (target database version assignment per file). On confirm, files are uploaded via XHR with concurrency control.

I used XHR instead of `fetch` because the Fetch API doesn't support upload progress events — XHR's `upload.onprogress` is the only way to get byte-level progress in the browser.

### Architecture

The upload infrastructure is built around an `UploadManager` class that encapsulates a Zustand store, concurrency semaphore, and XHR reference map for cancellation.

## Test

Unit tests for the upload manager covering lifecycle, cancellation, auto-clear, and concurrency. Mocked Playwright E2E tests covering the happy path, step navigation, file removal, error handling, and search/sort.

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

## Example (small fix)

```markdown
This PR fixes the layout of the section titles in the Application Assessment tab. The icon and text were misaligned because the flex container lacked `align-items: center`.

## Media

<img width="400" alt="before" src="..." />
<img width="400" alt="after" src="..." />

## References

- https://enterprisedb.atlassian.net/browse/MIG-7936
```
