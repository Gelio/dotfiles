---
name: diff-walkthrough
description: >
  Plan and lead a human through reviewing a local git diff for maximum
  comprehension — scope and triage the change, pick the right diff range,
  and order the walk so each file is legible when reached. Use before
  opening or reviewing a PR, when reviewing another engineer's branch
  checked out locally, or any time the user wants to understand a diff
  rather than have it auto-reviewed for bugs. Triggers on: "walk me
  through this diff", "help me review this branch", "review this diff",
  "understand these changes", "how should I review this",
  "/diff-walkthrough". Complements /code-review (which hunts bugs) and
  verify-branch-commits (which checks per-commit correctness) — this one
  optimizes a human's understanding.
argument-hint: '[diff-range]'
---

# Diff Walkthrough

Help a human understand a diff before they review it line-by-line. You are
not auto-reviewing for bugs (that's `/code-review`) — you are building the
map: what changed, how heavy each area is, and the order to read it so each
file makes sense by the time they reach it.

The output is a review *plan*, then the walk itself. Not a verdict.

## Process

### 1. Establish the diff range

Use `$0` if the user gave one. It may be:
- a full range — contains `..` (`main..HEAD`, `abc123..def456`) → use as-is
- a single base ref (`develop`, `v2.1`, a SHA) → review `<ref>..HEAD`

If no argument, **detect the default branch** and confirm before proceeding:
```bash
git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null   # e.g. origin/main
# fallback: whichever of main / master / develop exists
```
Then the range is `<base>..HEAD` (two-dot = the commits on this branch, not
on the base). Say which range you picked and why, so the user can correct a
wrong base (e.g. a release train instead of `main`) in one word.

### 2. Scope and triage — never assume uniform effort

```bash
git diff --stat <range>
git log --oneline <range>
```

Classify each file/area into a bucket. This is the most valuable step: it
stops the user spending equal attention on code that doesn't deserve it.

| Bucket | Signal | How to treat it |
|--------|--------|-----------------|
| **Novel logic** | new branches, algorithms, state, gating | Read closely — this is where bugs live |
| **Mechanical** | rename, signature threaded through callers, move | Skim; confirm it's really mechanical |
| **Generated / vendored** | `*.gen.*`, lockfiles, snapshots, `dist/` | Skip contents; note the line count is noise |
| **Backport / cherry-pick** | code that already lives + was reviewed elsewhere | Different question — see §4 |
| **Test-only** | scenarios, fixtures | Read after the logic they exercise |

A change that *looks* huge (e.g. +1000 lines) is often mostly generated or
backported. Say so explicitly — it reframes the whole review.

### 3. Order the walk by dependency, not alphabetically

Read **primitive → consumer**: the shared type / helper / core function
first, then the callers. That way each file is legible when reached instead
of referencing something not yet seen. Git's file order (alphabetical) almost
never matches this.

For each area, give the user the exact command to see just that slice:
```bash
git diff <range> -- <path>
```

Point to the one or two spots that earn real scrutiny (the tricky guard, the
new invariant, the edge case) rather than narrating every hunk.

### 4. Backports and generated files get a different baseline

- **Backport / cherry-pick**: the question isn't "is this good code" (it was
  reviewed upstream) — it's "is this a faithful copy + correct adaptation".
  Diff against the *source* branch, not the merge base, to surface only the
  adaptations:
  ```bash
  git diff <upstream-branch> -- <paths>     # what differs from the reviewed version
  git range-diff <upstream-range> <range>   # proves this == upstream minus adaptations
  ```
- **Generated files**: exclude from the walk entirely — reviewing them is
  wasted effort. Call out that they're generated and move on.

### 5. Squash awareness

If the branch has un-squashed `fixup!`/`squash!` commits, review the **net
diff** (`<range>`) for understanding — a commit-by-commit walk over fixups is
noisy and misleading. Note that a per-commit sanity pass (or
`verify-branch-commits`) belongs *after* the squash, not now.

## Output shape

Lead with the triage table (or a one-line-per-area equivalent) so the user
sees the shape and effort split immediately, then the ordered walk with the
per-slice commands. Keep it a map, not a lecture — the user does the reading;
you tell them where to look and what to look for.

Give a realistic effort estimate per area — it helps the user decide where to
spend a limited review budget.

## Worked example

`git diff --stat main..HEAD` shows +1240/−90 across 6 files; `git log` shows 4
commits including one `fixup!`. Don't take the size at face value — triage it:

**Range:** `main..HEAD` (default branch, 4 commits on this branch). One
`fixup!` present → walk the net diff, not commit-by-commit.

| Area | Bucket | Effort |
|------|--------|--------|
| `pnpm-lock.yaml` (+900) | Generated | Skip — the +900 is noise |
| `retry.ts` (new `backoff()`) | Novel logic | Read closely — the real change |
| `client.ts`, `worker.ts` (call `backoff()`) | Mechanical | Skim — confirm they just wire it in |
| `rename: fetchOne → fetchRow` (3 files) | Mechanical | Skim — signature threaded through |
| `retry.test.ts` | Test-only | Read after `retry.ts` |

So a "+1240" diff is really ~80 lines of new logic. Walk order (primitive →
consumer):

```bash
git diff main..HEAD -- src/retry.ts        # 1. the new backoff — jitter cap + max-attempts guard
git diff main..HEAD -- src/retry.test.ts   # 2. cases that pin its behavior
git diff main..HEAD -- src/client.ts src/worker.ts  # 3. skim the two call sites
```

Scrutinize one spot: the `Math.min(cap, base * 2**n)` guard in `backoff()` —
an off-by-one there retries forever. Everything else is wiring.
