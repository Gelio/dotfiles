---
name: route-decision-rationale
description: >
  Route the rationale behind a branch's design decisions to where a reviewer
  will actually see it, with a bias toward durable homes (in-code comment,
  README, PR description) and an inline PR comment only for the ephemeral,
  line-specific residue. Use when finishing a feature branch or opening/updating
  a PR that made non-obvious choices, when a decisions ledger / agent-plan with
  Q-decisions exists, or when the user says "surface the decisions", "document
  the rationale", "where should this rationale live", "route decision rationale",
  "/route-decision-rationale". Pairs with `pr-conventions` when drafting a PR
  description — invoke it whenever load-bearing reasoning is at risk of living
  only in commit bodies, which reviewers never read.
argument-hint: '[pr-or-branch] [ledger-path]'
---

# Route Decision Rationale

A reviewer reads three things: the diff, the PR description, and inline review
comments. They do **not** read commit message bodies. So a decision whose only
explanation lives in a commit body — or nowhere — is invisible, no matter how
carefully it was written. This skill walks the decisions made on a branch and
routes each one's rationale to a home where a reviewer will actually encounter
it, preferring homes that survive the merge.

The job is **routing**, not "posting inline comments." Inline comments are one
destination among several, and usually the least durable. Most decisions need
no action at all because their rationale is already visible.

## Routing destinations (most durable first)

| Destination | Lifespan | Use for |
|---|---|---|
| **In-code comment** | Permanent — travels with the line | A constraint, gotcha, or "why this and not the obvious alternative" that is local to a specific line or block. The first choice for anything line-anchored. |
| **README / module docs** | Permanent | Cross-cutting rationale that belongs with the subsystem and that future maintainers (not just this PR's reviewer) will need. |
| **PR description** | Survives as the PR record | The whole-PR narrative no single line anchors — the cross-cutting "how the pieces fit" a reviewer needs before reading the diff. Route here via `pr-conventions`. |
| **Inline PR review comment** | Ephemeral — read once, then buried in resolved conversations | A point tied to **one specific line** AND not worth persisting in shipped artifacts. The residue after everything durable has been routed away. |
| **SKIP** | — | The *specific* load-bearing rationale is already visible in the diff, an existing comment, the PR description, or adjacent docs. Do nothing — adding more just drowns the reviewer. (A comment that explains what a step *does* but omits the constraint or alternative that forced it is **not** "already visible" for that point — enrich it as a CODE edit instead of skipping.) |

The bias toward durable is deliberate: a code comment is read by everyone who
touches that line for years; an inline PR comment is read by one reviewer once
and then collapses into the resolved-conversations list. When a piece of
rationale could plausibly go in either, choose the durable home.

## Process

1. **Gather the decisions.** Pull from, in priority order:
   - A decisions ledger / agent-plan (`$1` ledger path, or look for `agent-plans/**/decisions.md`) — the explicit Q-decisions.
   - **The branch's commit message bodies** (`git log <base>..HEAD`). Mine these hard: load-bearing rationale (a constraint that forced the design, an alternative rejected, a non-obvious gotcha) routinely lives only here, which means it is currently invisible.
   - The diff itself — choices visible in the code but unexplained.

2. **Locate where each decision's rationale lives today.** For each one, answer: is this reasoning already somewhere a reviewer will see it (diff, existing comment, PR description, adjacent docs)?

3. **Classify the destination** using the table above:
   - Already visible → **SKIP**.
   - Line/block-local constraint or gotcha → **CODE comment**.
   - Cross-cutting, belongs with the subsystem → **README**.
   - Cross-cutting, whole-PR narrative → **PR-DESC**.
   - Line-specific AND ephemeral residue → **INLINE**.

4. **Drop anything that merely restates the code.** A comment or PR section has to add context the diff cannot show. If the proposed text just narrates the line, either cut it or move the *real* rationale (the why, the alternative, the constraint) to wherever that genuinely lives.

5. **Present every candidate, marked, and let the human trim.** Show a table: each decision, its proposed route, and one line of reasoning. Do not write or post anything yet — the human edits the routing first. This "show all marked, you trim" step is the point where over-eager surfacing gets caught before it reaches a reviewer.

6. **Execute the approved routing.**
   - CODE / README edits → as a focused `docs:` commit (one per repo). Frame the commit body as moving commit-only rationale into the file.
   - PR-DESC → fold into the description via `pr-conventions`.
   - INLINE → post the survivors as **one batched self-review**, not one comment at a time. The reviews endpoint takes an array of comment objects, so pass a JSON body on stdin (the `-f 'comments[][path]=…'` flag form does not reliably build an array of objects):
     ```bash
     gh api repos/<owner>/<repo>/pulls/<pr>/reviews --method POST --input - <<'JSON'
     {
       "event": "COMMENT",
       "comments": [
         { "path": "<file>", "line": <n>, "side": "RIGHT", "body": "<text>" }
       ]
     }
     JSON
     ```

## Pairing with `pr-conventions`

When this runs alongside `pr-conventions` for a PR-description draft, also emit
the list of **planned post-creation inline comments** next to the description.
That way the person reviewing the draft sees what is deliberately *not* in the
PR body because it will surface as a line-specific comment instead — nothing
falls through the gap between the two skills.

## Non-negotiables

- **Commit-only rationale is invisible — re-home it.** This is the whole reason the skill exists. Always mine commit bodies; never leave a decision's only explanation in `git log`.
- **Skip what's already visible — but judge the rationale, not the line.** Surfacing reasoning a reviewer can already see costs their attention for no gain; less is more. The test is whether the *specific* load-bearing point (the constraint, the rejected alternative, the gotcha) is visible — not merely whether the line happens to carry a comment. A step commented with what it does, but silent on the constraint that forced it, still needs that constraint surfaced.
- **Cap inline comment bodies at ~6 sentences.** Compress to the rationale plus the alternative considered. A reviewer skims; a wall of text is a skipped comment.
- **Never plain-text-path a gitignored ledger, and don't permalink one** — agent-plans are typically gitignored, so the link 404s. Make each surfaced comment self-contained instead. Permalink a ledger only when it is actually committed and reachable.
- **Inline comments go as a single batched review**, so the reviewer gets one notification and one coherent pass, not a drip of separate comments.

## Example — MIG-8939 (the pattern that produced this skill)

Input: a 16-entry decisions ledger (Q1–Q16) plus two PR branches. Outcome after routing:

- **Most Q-decisions → SKIP.** Their rationale was already in the diff, an existing comment, or the PR body.
- **AWS-auth reasoning → CODE comments (2 `docs` commits).** It had lived only in commit bodies. Moved into `run-tests.yaml` (the OIDC/appliance-dev two-layer model, the RKE cross-account-SCP constraint that makes a pillar role fail with `AccessDenied`, the artifact-name uniqueness reason) and into `e2e-tests.yaml` (the skip is portal-reachability, not auth).
- **Cross-cutting narrative → PR-DESC.** The per-pillar-OIDC-with-appliance-dev-fallback story and the EKS-on-centralized-network descope went into both PR descriptions, where no single line anchored them.
- **One decision → a dropped candidate.** A proposed comment on the `Add aws profile for pillar migration` step was cut because it merely restated the code; its real rationale went to the PR description instead.
- **Exactly one decision → INLINE.** The `e2e-nexus-test` display-name choice ("Migration Nexus E2E", because the Migration team has multiple squads) plus the `needs: [setup]`-only reasoning — line-specific and not worth shipping in a code comment. One comment, on one line, in one batched review.

The lesson encoded above: of sixteen decisions, the right call was fifteen
durable-or-skip and a single inline comment. Reaching for an inline comment per
decision would have buried the reviewer; routing each to its most durable home
kept the signal high.
