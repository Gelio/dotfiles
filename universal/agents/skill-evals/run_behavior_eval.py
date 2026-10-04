#!/usr/bin/env python3
"""Behavior benchmark for skills: does an output FOLLOW the skill better than baseline?

For each scenario we run the model twice — once with the skill body injected
("with_skill"), once without ("without_skill") — then grade each output against
the scenario's assertions. The delta in pass-rate is the skill's measured value.

The model runs in an ISOLATED, cheap context so the only difference between the
two conditions is the skill text itself:

    --system-prompt          replace the default Claude Code system prompt
    --tools ""               no tools; the model emits the artifact as text
    --strict-mcp-config      drop all MCP servers (~66k tokens of tool defs)
    --setting-sources ""     load no user/project/local settings (no other skills)
    --disable-slash-commands no skills auto-resolve into context
    --no-session-persistence don't litter ~/.claude with sessions

Output is written in the workspace layout that skill-creator's
aggregate_benchmark.py and eval-viewer/generate_review.py consume, so the
existing stats + HTML viewer are reused rather than reimplemented.

Network note: `claude -p` must reach api.anthropic.com, which is outside the
default command sandbox — run this script with the sandbox disabled.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TypedDict, cast

HERE = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# JSON shapes (eval spec files and the claude CLI envelope)
# ---------------------------------------------------------------------------


class _AssertionBase(TypedDict):
    type: str
    text: str


class Assertion(_AssertionBase, total=False):
    # Present only for the assertion types that use them.
    needle: str
    pattern: str
    ignorecase: bool


class _ScenarioBase(TypedDict):
    id: int
    prompt: str
    assertions: list[Assertion]


class Scenario(_ScenarioBase, total=False):
    name: str
    kind: str


class Spec(TypedDict):
    skill: str
    skill_path: str
    scenarios: list[Scenario]


class ClaudeResult(TypedDict, total=False):
    is_error: bool
    result: str
    subtype: str
    structured_output: object
    total_cost_usd: float


class Expectation(TypedDict):
    text: str
    passed: bool
    evidence: str


class Summary(TypedDict):
    passed: int
    failed: int
    total: int
    pass_rate: float


class _GradingBase(TypedDict):
    expectations: list[Expectation]
    summary: Summary


class Grading(_GradingBase, total=False):
    # Added after grading, in run_one.
    timing: dict[str, float]
    execution_metrics: dict[str, int]
    _cost_usd: float


class RunResult(TypedDict):
    condition: str
    run_idx: int
    output: str
    grading: Grading


class JudgeVerdict(TypedDict):
    index: int
    passed: bool
    evidence: str


# ---------------------------------------------------------------------------
# SKILL.md parsing (self-contained — no dependency on skill-creator's package)
# ---------------------------------------------------------------------------


def parse_skill_md(skill_md: Path) -> tuple[str, str, str]:
    """Return (name, description, body) where body is the content after the
    frontmatter — that is what gets loaded when a skill fires."""
    text = skill_md.read_text()
    lines = text.split("\n")
    if lines[0].strip() != "---":
        raise ValueError(f"{skill_md} missing opening frontmatter ---")
    end: int | None = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError(f"{skill_md} missing closing frontmatter ---")

    name, description = "", ""
    fm = lines[1:end]
    i = 0
    while i < len(fm):
        line = fm[i]
        if line.startswith("name:"):
            name = line[len("name:") :].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:") :].strip()
            if value in (">", "|", ">-", "|-"):
                cont: list[str] = []
                i += 1
                while i < len(fm) and (
                    fm[i].startswith("  ") or fm[i].startswith("\t")
                ):
                    cont.append(fm[i].strip())
                    i += 1
                description = " ".join(cont)
                continue
            description = value.strip('"').strip("'")
        i += 1

    body = "\n".join(lines[end + 1 :]).strip()
    return name, description, body


# ---------------------------------------------------------------------------
# Isolated claude -p invocation
# ---------------------------------------------------------------------------

BASE_SYSTEM = (
    "You are an AI coding assistant helping an experienced software engineer. "
    "Complete the user's request directly and concisely. When they ask you to "
    "write an artifact — a git commit message, a pull request description, a "
    "Jira description, edited file contents, and so on — output the final "
    "artifact text itself, not a description of what you would write. Do not "
    "ask clarifying questions; make reasonable assumptions and proceed."
)

SKILL_WRAPPER = (
    '\n\n<active_skill name="{name}">\n'
    "The following skill is active for this task. Follow its instructions:\n\n"
    "{body}\n"
    "</active_skill>"
)


def run_claude(
    model: str,
    system: str,
    prompt: str,
    timeout: int = 240,
    json_schema: str | None = None,
) -> ClaudeResult:
    """Run one isolated headless turn. Returns parsed JSON result dict."""
    args = [
        "claude",
        "--print",
        "--model",
        model,
        "--tools",
        "",
        "--strict-mcp-config",
        "--setting-sources",
        "",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--output-format",
        "json",
        "--system-prompt",
        system,
    ]
    if json_schema:
        args += ["--json-schema", json_schema]
    args.append(prompt)

    # Strip CLAUDECODE so the nested CLI doesn't bail on the interactive guard.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    if not proc.stdout.strip():
        raise RuntimeError(f"empty claude output; stderr: {proc.stderr[:500]}")
    parsed = cast(ClaudeResult, json.loads(proc.stdout))
    if parsed.get("is_error"):
        raise RuntimeError(
            f"claude error: {parsed.get('result') or parsed.get('subtype')}"
        )
    return parsed


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

# Broad emoji / pictograph ranges — enough to catch 🚀✅🤖 etc. in PR/commit text.
EMOJI_RE = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff←-⇿⬀-⯿️]"
)

JUDGE_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer"},
                        "passed": {"type": "boolean"},
                        "evidence": {"type": "string"},
                    },
                    "required": ["index", "passed", "evidence"],
                },
            }
        },
        "required": ["results"],
    }
)


def grade_mechanical(assertion: Assertion, output: str) -> tuple[bool, str]:
    """Evaluate a deterministic assertion. Returns (passed, evidence)."""
    t = assertion["type"]
    if t == "contains":
        needle = assertion.get("needle", "")
        ok = needle in output
        return ok, f"substring {'found' if ok else 'not found'}: {needle!r}"
    if t == "not_contains":
        needle = assertion.get("needle", "")
        ok = needle not in output
        return ok, f"substring {'absent' if ok else 'present'}: {needle!r}"
    if t == "regex":
        pattern = assertion.get("pattern", "")
        flags = (
            re.MULTILINE | re.IGNORECASE
            if assertion.get("ignorecase")
            else re.MULTILINE
        )
        m = re.search(pattern, output, flags)
        return bool(m), (
            f"matched {m.group(0)!r}" if m else f"no match for /{pattern}/"
        )
    if t == "not_regex":
        pattern = assertion.get("pattern", "")
        flags = (
            re.MULTILINE | re.IGNORECASE
            if assertion.get("ignorecase")
            else re.MULTILINE
        )
        m = re.search(pattern, output, flags)
        return (not m), (
            f"unexpected match {m.group(0)!r}" if m else "no forbidden match (good)"
        )
    if t == "no_emoji":
        m = EMOJI_RE.search(output)
        return (not m), (f"emoji found: {m.group(0)!r}" if m else "no emoji")
    raise ValueError(f"unknown mechanical assertion type: {t}")


def grade_output(output: str, assertions: list[Assertion], judge_model: str) -> Grading:
    """Grade one output against all its assertions, returning a grading.json dict."""
    expectations: list[Expectation | None] = [None] * len(assertions)
    judge_items: list[tuple[int, str]] = []  # (orig_index, text)

    for i, a in enumerate(assertions):
        if a["type"] == "judge":
            judge_items.append((i, a["text"]))
        else:
            passed, evidence = grade_mechanical(a, output)
            expectations[i] = {
                "text": a["text"],
                "passed": passed,
                "evidence": evidence,
            }

    if judge_items:
        numbered = "\n".join(f"{n}. {text}" for n, (_, text) in enumerate(judge_items))
        judge_prompt = (
            "You are a strict grader. Below is an OUTPUT produced by an AI assistant, "
            "followed by a numbered list of CRITERIA. For each criterion, decide whether "
            "the output satisfies it. Be strict and literal: if a criterion is not clearly "
            "met, mark it failed. Judge only what the criterion asks about.\n\n"
            'Return JSON: {"results": [{"index": <criterion number>, "passed": <bool>, '
            '"evidence": "<short quote or reason>"}, ...]} with one entry per criterion.\n\n'
            f"=== OUTPUT ===\n{output}\n\n=== CRITERIA ===\n{numbered}\n"
        )
        verdict = run_claude(
            judge_model,
            "You are a meticulous evaluation grader. Respond only with the requested JSON.",
            judge_prompt,
            json_schema=JUDGE_SCHEMA,
        )
        # With --json-schema the validated object is returned under
        # "structured_output" (not "result", which is empty in that mode).
        structured_raw = verdict.get("structured_output")
        structured: dict[str, object]
        if isinstance(structured_raw, dict):
            structured = cast(dict[str, object], structured_raw)
        else:
            loaded: object
            try:
                loaded = cast(object, json.loads(verdict.get("result") or "{}"))
            except (json.JSONDecodeError, TypeError):
                loaded = {}
            structured = (
                cast(dict[str, object], loaded) if isinstance(loaded, dict) else {}
            )
        raw_results = structured.get("results", [])
        results_list = (
            cast(list[JudgeVerdict], raw_results)
            if isinstance(raw_results, list)
            else []
        )
        by_index = {jv["index"]: jv for jv in results_list}
        for n, (orig_i, text) in enumerate(judge_items):
            r = by_index.get(n)
            if r is None:
                expectations[orig_i] = {
                    "text": text,
                    "passed": False,
                    "evidence": "judge returned no verdict",
                }
            else:
                expectations[orig_i] = {
                    "text": text,
                    "passed": bool(r["passed"]),
                    "evidence": r.get("evidence", ""),
                }

    exps = [e for e in expectations if e is not None]
    passed = sum(1 for e in exps if e["passed"])
    total = len(exps)
    return {
        "expectations": exps,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "pass_rate": round(passed / total, 4) if total else 0.0,
        },
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_one(
    skill_body: str,
    skill_name: str,
    scenario: Scenario,
    condition: str,
    run_idx: int,
    gen_model: str,
    judge_model: str,
) -> RunResult:
    """Run + grade a single (scenario, condition, run) cell."""
    system = BASE_SYSTEM
    if condition == "with_skill":
        system += SKILL_WRAPPER.format(name=skill_name, body=skill_body)

    t0 = time.time()
    res = run_claude(gen_model, system, scenario["prompt"])
    elapsed = time.time() - t0
    output = res.get("result", "")

    grading = grade_output(output, scenario["assertions"], judge_model)
    grading["timing"] = {"total_duration_seconds": round(elapsed, 1)}
    grading["execution_metrics"] = {
        "output_chars": len(output),
        "total_tool_calls": 0,
        "errors_encountered": 0,
    }
    grading["_cost_usd"] = res.get("total_cost_usd", 0)
    return {
        "condition": condition,
        "run_idx": run_idx,
        "output": output,
        "grading": grading,
    }


def run_skill(
    eval_file: Path,
    out_dir: Path,
    gen_model: str,
    judge_model: str,
    runs: int,
    concurrency: int,
) -> tuple[Path, str]:
    spec = cast(Spec, json.loads(eval_file.read_text()))
    skill_name = spec["skill"]
    skill_md = (eval_file.parent / spec["skill_path"]).resolve()
    name, _desc, body = parse_skill_md(skill_md)

    iteration_dir = out_dir / "iteration-1"
    iteration_dir.mkdir(parents=True, exist_ok=True)

    # Build the full task list (scenario × condition × run).
    tasks: list[tuple[Scenario, str, int]] = []
    for sc in spec["scenarios"]:
        for condition in ("with_skill", "without_skill"):
            for r in range(1, runs + 1):
                tasks.append((sc, condition, r))

    print(
        (
            f"[{skill_name}] {len(spec['scenarios'])} scenarios × 2 conditions × "
            f"{runs} runs = {len(tasks)} generations (gen={gen_model}, judge={judge_model})"
        ),
        file=sys.stderr,
    )

    results: list[tuple[Scenario, str, int, RunResult]] = []
    total_cost = 0.0
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        fut_to_task: dict[Future[RunResult], tuple[Scenario, str, int]] = {
            ex.submit(run_one, body, name, sc, cond, r, gen_model, judge_model): (
                sc,
                cond,
                r,
            )
            for (sc, cond, r) in tasks
        }
        done = 0
        for fut in as_completed(fut_to_task):
            sc, cond, r = fut_to_task[fut]
            done += 1
            try:
                out = fut.result()
                cost = out["grading"].pop("_cost_usd", 0)
                total_cost += cost
                pr = out["grading"]["summary"]["pass_rate"]
                print(
                    (
                        f"  [{done}/{len(tasks)}] eval-{sc['id']} {cond} run-{r}: "
                        f"{pr * 100:.0f}% (${cost:.3f})"
                    ),
                    file=sys.stderr,
                )
                results.append((sc, cond, r, out))
            except Exception as e:
                print(
                    f"  [{done}/{len(tasks)}] eval-{sc['id']} {cond} run-{r}: FAILED {e}",
                    file=sys.stderr,
                )

    # Write workspace layout.
    for sc in spec["scenarios"]:
        eval_dir = iteration_dir / f"eval-{sc['id']}"
        eval_dir.mkdir(parents=True, exist_ok=True)
        _ = (eval_dir / "eval_metadata.json").write_text(
            json.dumps(
                {
                    "eval_id": sc["id"],
                    "eval_name": sc.get("name", f"eval-{sc['id']}"),
                    "kind": sc.get("kind", "core"),
                    "prompt": sc["prompt"],
                    "assertions": [a["text"] for a in sc["assertions"]],
                },
                indent=2,
            )
        )

    for sc, cond, r, out in results:
        run_dir = iteration_dir / f"eval-{sc['id']}" / cond / f"run-{r}"
        # The viewer (generate_review.py) discovers a run by the presence of an
        # outputs/ subdir, and reads grading.json from the run dir itself.
        outputs_dir = run_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        _ = (outputs_dir / "output.md").write_text(out["output"])
        _ = (run_dir / "grading.json").write_text(json.dumps(out["grading"], indent=2))
        # The viewer reads the prompt from eval_metadata.json at the run dir or
        # its parent, so drop a copy alongside the run.
        _ = (run_dir / "eval_metadata.json").write_text(
            json.dumps(
                {
                    "eval_id": sc["id"],
                    "eval_name": sc.get("name", f"eval-{sc['id']}"),
                    "prompt": sc["prompt"],
                },
                indent=2,
            )
        )

    print(f"[{skill_name}] total cost ${total_cost:.3f}", file=sys.stderr)
    return iteration_dir, name


class Args(argparse.Namespace):
    # Defaults mirror the argparse definitions below; argparse overwrites them
    # on the instance. They exist so the attributes are typed and initialized.
    skills: list[str] = []
    gen_model: str = "sonnet"
    judge_model: str = "sonnet"
    runs: int = 3
    concurrency: int = 4
    no_viewer: bool = False


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    _ = ap.add_argument(
        "skills",
        nargs="*",
        help="Skill names to eval (default: all in evals/). e.g. pr-conventions",
    )
    _ = ap.add_argument(
        "--gen-model",
        default="sonnet",
        help=(
            "Model that produces the artifacts (default: sonnet). "
            "Use 'opus' to match your interactive sessions."
        ),
    )
    _ = ap.add_argument(
        "--judge-model",
        default="sonnet",
        help="Model that grades judge-type assertions (default: sonnet).",
    )
    _ = ap.add_argument(
        "--runs", type=int, default=3, help="Runs per condition (default: 3)."
    )
    _ = ap.add_argument(
        "--concurrency", type=int, default=4, help="Parallel claude calls (default: 4)."
    )
    _ = ap.add_argument(
        "--no-viewer", action="store_true", help="Skip the HTML viewer."
    )
    args = ap.parse_args(namespace=Args())

    evals_dir = HERE / "evals"
    if args.skills:
        eval_files = [evals_dir / f"{s}.json" for s in args.skills]
    else:
        eval_files = sorted(evals_dir.glob("*.json"))

    missing = [str(f) for f in eval_files if not f.exists()]
    if missing:
        print(f"Eval file(s) not found: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    timestamp = time.strftime("%Y-%m-%d_%H%M%S")
    aggregate = HERE / "vendor" / "aggregate_benchmark.py"
    viewer = HERE / "vendor" / "generate_review.py"

    for eval_file in eval_files:
        skill_slug = eval_file.stem
        out_dir = HERE / "runs" / f"{skill_slug}_{timestamp}"
        iteration_dir, name = run_skill(
            eval_file,
            out_dir,
            args.gen_model,
            args.judge_model,
            args.runs,
            args.concurrency,
        )

        # Aggregate stats via the reused skill-creator script.
        _ = subprocess.run(
            [sys.executable, str(aggregate), str(iteration_dir), "--skill-name", name],
            check=False,
        )

        benchmark_json = iteration_dir / "benchmark.json"
        # aggregate_benchmark.py hardcodes a placeholder model name and
        # runs_per_configuration=3; correct them to this run's actual values.
        if benchmark_json.exists():
            data = cast(dict[str, object], json.loads(benchmark_json.read_text()))
            metadata = cast(dict[str, object], data.get("metadata") or {})
            metadata["executor_model"] = args.gen_model
            metadata["analyzer_model"] = args.judge_model
            metadata["runs_per_configuration"] = args.runs
            data["metadata"] = metadata
            _ = benchmark_json.write_text(json.dumps(data, indent=2))
        if not args.no_viewer and benchmark_json.exists():
            static_html = out_dir / "review.html"
            _ = subprocess.run(
                [
                    sys.executable,
                    str(viewer),
                    str(iteration_dir),
                    "--skill-name",
                    name,
                    "--benchmark",
                    str(benchmark_json),
                    "--static",
                    str(static_html),
                ],
                check=False,
            )
            print(f"\nReview: {static_html}", file=sys.stderr)

        # Print the markdown summary inline.
        bench_md = iteration_dir / "benchmark.md"
        if bench_md.exists():
            print("\n" + bench_md.read_text(), file=sys.stderr)


if __name__ == "__main__":
    main()
