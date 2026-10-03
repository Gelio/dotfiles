---
name: pr-comments
description: >
  Write and reply to GitHub PR review comments matching the user's preferred
  style — SHA-pinned permalinks for code, linked ticket IDs, in-thread replies.
  Use this whenever drafting or replying to a PR review comment (inline or
  review-body), leaving a comment on a PR or issue, responding to review
  feedback, or working a pending/draft review — even if the user doesn't say
  "skill". Triggers on "PR comment", "review comment", "reply to review",
  "reply to this comment", "leave a comment on the PR", "draft review",
  "pending review", "respond to the reviewer".
  Layers on top of `jira-preferences` (permalink + SHA-selection mechanics),
  `pr-conventions` (PR descriptions), and `commit-conventions` (commit messages).
---

# PR Review Comment Conventions

This governs **new** PR review comments and replies — inline comments, review-body
text, issue comments, and pending-review comments. It does not cover PR
*descriptions* (`pr-conventions`) or commit messages (`commit-conventions`). Don't
retroactively rewrite already-posted comments unless the user asks.

The recurring failure this skill prevents: defaulting to plain Markdown — bare
backticks for a code location, raw `MIG-1234`, prose line numbers like "L123" or
"~line 201". A reviewer can't click any of those. The fixes below all serve one
goal: every reference the reader might want to follow is a real, durable link.

## Non-negotiables

1. **A code *location* is always a SHA-pinned permalink — never a bare path, prose
   line number, or backticks alone.** Backticks are fine for a short inline
   *identifier* (`ErrorAttr`, `validatePostgresProceduralLanguages`), but the
   moment you point at *where* something lives (file, line, range, SQL migration,
   workflow step), it gets a permalink. The mechanics — permalink shape and how to
   pick the SHA — live in `jira-preferences` ("Permalinks for code references");
   reuse them, don't restate. In short: `https://github.com/<org>/<repo>/blob/<sha>/<path>#L<n>-L<m>`,
   and pick the SHA deliberately — work-in-progress → the feature branch tip
   that's already on `origin` (pre-push SHAs 404); present state → `main` HEAD;
   history → the introducing commit. Never `blob/main/…` — it shifts as `main`
   advances.
2. **Ticket references are linked, never bare.** `[MIG-1234](https://enterprisedb.atlassian.net/browse/MIG-1234)`,
   not `MIG-1234`. A bare key forces the reader to go find it themselves.
3. **PR/issue references**: `#123` auto-links within the same repo; cross-repo
   references get the full URL.
4. **No hard line wrapping.** Each paragraph is one long line — GitHub wraps it.
   Hard-wrapped lines render with broken mid-sentence breaks on wide viewports.
   (Same rule as `pr-conventions` NN#9; the 72-col commit wrap does not apply here.)
5. **No emoji** unless the user explicitly wants them.
6. **Tone: concise, specific, evidence-first.** Lead with the concrete observation
   and point at the code; skip throat-clearing. State confidence honestly —
   distinguish a blocker from an open question.

## Replies to existing threads — stay in the thread

When responding to an existing review comment, post the reply **in that same
thread**, not as a new top-level comment on the current diff — **even when the
thread is anchored to an outdated diff or a line that has since moved.**

GitHub keeps a reply attached to its thread regardless of how stale the anchor is.
A fresh top-level comment, by contrast, orphans the discussion: the reviewer loses
the back-and-forth that gave the point its context, and the original thread sits
unresolved forever. Keeping the conversation in one place is worth more than
anchoring to the latest line.

```bash
# Reply in-thread to review comment <id> (preferred for any response):
gh api repos/<org>/<repo>/pulls/<pr>/comments/<id>/replies \
  -f body='Fixed in <permalink> — switched the sort to operate on a copy.'
```

Only start a **new** thread when the point is genuinely new — not a response to an
existing one.

## Pending / draft reviews

To collect several comments before submitting, create the review with **no `event`**
so it stays `PENDING`; the user keeps adding comments and submits later. Don't
auto-submit (`APPROVE` / `REQUEST_CHANGES` / `COMMENT`) unless the user says to —
submitting is theirs to trigger.

## Permalink anchor text

Use descriptive anchor text the reader can scan without hovering — the symbol name
when you're pointing at one, otherwise `file:line`. Mirror the `jira-preferences`
pattern: an inline-code identifier followed by a linked location. Don't put the
`code` span *inside* the link text.

Good: ``the sort in `sortProceduralLanguagesByName` ([scenario_183.go:412](https://github.com/EnterpriseDB/nexus-tests/blob/6f017fb/test-runner/pkg/testscenarios/scenario_183.go#L412)) mutates the caller's slice``

## Before / after

**Pointing at a code location**

Before (don't): The nil guard in `validatePostgresProceduralLanguages` at ~line 201 is inconsistent with the other validator.

After (do): The nil guard in `validatePostgresProceduralLanguages` ([scenario_183.go:201](https://github.com/EnterpriseDB/nexus-tests/blob/6f017fb/test-runner/pkg/testscenarios/scenario_183.go#L201)) is inconsistent with `validatePostgisExtension` ([scenario_183.go:248](https://github.com/EnterpriseDB/nexus-tests/blob/6f017fb/test-runner/pkg/testscenarios/scenario_183.go#L248)) — both share the caller's non-nil guarantee, so either both guard or neither should.

**Referencing a ticket**

Before (don't): Please apply the MIG-9641 rules on the Markdown test scenario.

After (do): Please apply the [MIG-9641](https://enterprisedb.atlassian.net/browse/MIG-9641) rules on the Markdown test scenario.

**Replying to a stale thread**

The reviewer's comment is anchored to a line that the latest force-push moved. Reply
*in the thread* (not a new comment on the new line):

> Fixed — the sort now operates on a copy ([scenario_183.go:415](https://github.com/EnterpriseDB/nexus-tests/blob/<new-sha>/test-runner/pkg/testscenarios/scenario_183.go#L415)). Keeping this here on the original thread so the discussion stays together.

## Related skills

- **`jira-preferences`** — canonical permalink shape + SHA-selection mechanics (the source of truth this skill reuses), and Jira-ticket linking.
- **`pr-conventions`** — PR *descriptions* (not comments).
- **`commit-conventions`** — commit messages.
- **`route-decision-rationale`** — when a branch's decisions need routing to durable homes, including which inline PR comments to leave.
