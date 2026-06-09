# skill-evals — behavior benchmark for my skills

Measures whether each skill's **body** actually changes model behavior: for every
scenario the harness runs the model twice — once with the skill injected
(`with_skill`), once without (`without_skill`) — grades both outputs against a
checklist of assertions, and reports the pass-rate delta. The delta is the
skill's measured value.

This answers *"does the skill work when it's active?"* It does **not** measure
whether the skill *fires* (triggering/activation) — that's a separate harness.

## How it works

```
                    ┌─────────────────────────────┐
   scenario prompt ─┬─► claude WITHOUT skill ──────► output A ─► grade ─► e.g. 3/8
                    └─► claude WITH skill body ────► output B ─► grade ─► e.g. 8/8
                                                                  delta = +5/8
```

Each side runs in an **isolated, cheap context** so the only variable is the
skill text. The flags that achieve this (in `run_behavior_eval.py`):

    --system-prompt          replace the default Claude Code system prompt
    --tools ""               no tools; the model emits the artifact as text
    --strict-mcp-config      drop all MCP servers (~66k tokens of tool defs)
    --setting-sources ""     load no settings — none of my other ~25 skills leak in
    --disable-slash-commands no skills auto-resolve into context

Grading is two kinds of assertion:

- **Mechanical** (`contains`, `not_contains`, `regex`, `not_regex`, `no_emoji`) —
  evaluated in-process. Free, instant, deterministic.
- **`judge`** — a second `claude` call reads the output and rules pass/fail with a
  one-line reason. Used only for things a regex can't check ("explains *why*, not
  *what*"; "References section is last").

Output is written in the layout that skill-creator's `aggregate_benchmark.py` and
`eval-viewer/generate_review.py` expect, which are vendored under `vendor/` so this
harness is self-contained.

## Running it

`claude -p` must reach `api.anthropic.com`, which is outside the default command
sandbox, **and** the harness writes under `runs/` — so run it with the sandbox
disabled (in Claude Code, approve the unsandboxed Bash call).

```bash
cd universal/claude/skill-evals

# One skill, quick + cheap (1 run each, haiku) — pipeline check, not a real measurement
python3 run_behavior_eval.py pr-conventions --runs 1 --gen-model haiku --judge-model haiku

# A real measurement on the model you actually use, 3 runs each for variance
python3 run_behavior_eval.py pr-conventions --gen-model opus --judge-model sonnet --runs 3

# All skills
python3 run_behavior_eval.py --gen-model opus --judge-model sonnet --runs 3
```

Flags: `--gen-model` (artifact author, default `sonnet`), `--judge-model`
(grader, default `sonnet`), `--runs` (per condition, default 3), `--concurrency`
(default 4), `--no-viewer`.

**Model choice matters.** Grade against the model you actually run skills under
(`--gen-model opus`) — a skill that a strong model follows effortlessly may still
fail on a weaker one, and vice-versa. `sonnet` is a reasonable, cheaper judge.

## Reading the output

Each run writes to `runs/<skill>_<timestamp>/`:

- `iteration-1/benchmark.json` / `benchmark.md` — the stats table (pass rate
  mean ± stddev, time, tokens, and the delta).
- `review.html` — open in a browser. Two tabs: **Outputs** (click through each
  with/without output and its per-assertion grades) and **Benchmark** (the stats).
- `iteration-1/eval-N/<condition>/run-K/outputs/output.md` — the raw model output.
- `.../run-K/grading.json` — per-assertion pass/fail + evidence.

### What the numbers tell you (the optimization loop)

- **Low baseline, high with-skill** → the skill adds real value; keep it.
- **An assertion at 0% even with the skill** → the skill is failing to teach that
  rule. Edit the skill body, re-run, watch it climb.
- **An assertion already ~100% without the skill** → the model does it anyway;
  that rule is dead weight you can cut for context budget.
- **with_skill < without_skill on an assertion** → the skill is actively *hurting*
  (a regression). Fix immediately.

That is the skill-optimizer loop: **measure → find the failing check → edit →
measure again.**

## Caveats

- **Procedural skills are lower-signal.** `commit-conventions`, `pr-conventions`,
  `jira-preferences`, and `enrich-todos` produce a concrete text artifact, which
  grades cleanly. `todos` and `verify-branch-commits` are orchestration workflows
  with no single artifact — their scenarios grade the *plan the model describes*,
  which is a weaker proxy than observing the real run. Treat their deltas as a
  sanity check, not gospel.
- **Judge noise.** Judge assertions inherit the grader model's mistakes. Skim
  `grading.json` evidence on surprising results; rephrase the assertion if the
  judge misread it.
- **`benchmark.md` metadata.** The vendored aggregator writes a placeholder model
  name and `3 runs` into `benchmark.md`; `benchmark.json` (what the viewer uses)
  is corrected by the runner. Trust the viewer / JSON over the `.md` header.

## Authoring scenarios

One JSON file per skill in `evals/<skill-name>.json`:

```json
{
  "skill": "pr-conventions",
  "skill_path": "../../stowed/.claude/skills/pr-conventions/SKILL.md",
  "scenarios": [
    {
      "id": 1,
      "name": "feature-pr",
      "kind": "core",
      "prompt": "Write a PR description for ...",
      "assertions": [
        {"text": "Begins with 'This PR'", "type": "regex", "pattern": "^\\s*This PR\\b"},
        {"text": "No emoji", "type": "no_emoji"},
        {"text": "Technical choices woven into the narrative", "type": "judge"}
      ]
    }
  ]
}
```

`kind` is just a label (`core` / `omission` / `noisy`) for your own reference —
omission scenarios test footers/rules that are easy to drop; noisy scenarios bury
the real ask in distractor context. Prefer mechanical assertions where possible;
reach for `judge` only when meaning, not surface text, is what matters.

## Development

Dev tooling (`ruff`, `basedpyright`) is declared as a uv dependency group in
`pyproject.toml` and pinned by `uv.lock` — deliberately not sourced from the
editor's Mason install, so the harness lints reproducibly on its own.

```bash
uv sync                              # create .venv with the dev tools
uv run ruff format run_behavior_eval.py
uv run ruff check run_behavior_eval.py
uv run basedpyright                  # strict; vendor/ and runs/ are excluded
```

`run_behavior_eval.py` is fully typed and clean under basedpyright's default
(strict) mode. `vendor/` is vendored third-party code from skill-creator and is
not linted or type-checked.
