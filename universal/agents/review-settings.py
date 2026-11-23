#!/usr/bin/env python3
"""Review ~/.claude/settings.json for items to adopt into settings-partial.json.

For each live value that neither the partial nor this machine's overlay
(~/.config/dotfiles/local/.claude/settings.json, see mise/merge_local.py)
already contributes, prompt:
  [a]dopt  - write the item into settings-partial.json
  [l]ocal  - write the item into the overlay, for this machine only
  [s]kip   - skip for this run (ask again next time)
  [i]gnore - add to .settings-review-ignore.json (never ask again)
  [q]uit   - stop reviewing and save what's been chosen so far

The mise merge entry replaces arrays whole, so adopt or localize live-only items
before `mise dot apply` (mise/merge-guard.py lists them and stops the apply).
Objects are walked per leaf, arrays are diffed by value, and `hooks` is walked
matcher by matcher and command by command.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "mise"))
import merge_local

SETTINGS = Path.home() / ".claude/settings.json"
PARTIAL = ROOT / "settings-partial.json"
OVERLAY = merge_local.overlay_path(SETTINGS)
IGNORE = ROOT / ".settings-review-ignore.json"


def compact(value) -> str:
    """Match JSON.stringify so existing ignore keys stay valid."""
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def same_hook(a: dict, b: dict) -> bool:
    return (a.get("type"), a.get("command"), a.get("if")) == (
        b.get("type"),
        b.get("command"),
        b.get("if"),
    )


def find_candidates(partial: dict, live: dict):
    """Yield (ignore key, heading, body, apply) for each item missing from the partial."""
    for key, value in live.items():
        if key == "hooks":
            yield from hook_candidates(partial.get("hooks") or {}, value)
        else:
            yield from value_candidates([key], partial.get(key), value)


def value_candidates(path: list[str], partial, live):
    dotted = ".".join(path)
    if isinstance(live, dict):
        for key, value in live.items():
            yield from value_candidates(
                [*path, key],
                partial.get(key) if isinstance(partial, dict) else None,
                value,
            )
    elif isinstance(live, list):
        existing = partial if isinstance(partial, list) else []
        for item in live:
            if item not in existing:
                yield (
                    f"{dotted}[]:{compact(item)}",
                    f"Append to {dotted}",
                    item,
                    lambda p, i=item: container(p, path, []).append(i),
                )
    elif compact(partial) != compact(live):

        def assign(p, value=live):
            container(p, path[:-1], {})[path[-1]] = value

        yield dotted, f"Set {dotted}", live, assign


def hook_candidates(partial: dict, live: dict):
    for event, matchers in live.items():
        for matcher in matchers:
            pattern = matcher.get("matcher", "")
            label = f"hooks.{event}[matcher={compact(pattern)}]"
            # The overlay can add a second matcher with the same pattern
            same = [
                m for m in partial.get(event, []) if m.get("matcher", "") == pattern
            ]
            existing = [h for m in same for h in m.get("hooks", [])]
            if not same:
                yield (
                    label,
                    f"Add hook matcher  {label}",
                    matcher,
                    lambda p, e=event, m=matcher: container(p, ["hooks", e], []).append(
                        m
                    ),
                )
                continue
            for hook in matcher.get("hooks", []):
                if any(same_hook(h, hook) for h in existing):
                    continue
                key = {k: hook[k] for k in ("type", "command", "if") if hook.get(k)}
                yield (
                    f"{label}.hooks:{compact(key)}",
                    f"Add hook command  {label}",
                    hook,
                    lambda p, e=event, pat=pattern, h=hook: add_hook(p, e, pat, h),
                )


def container(root: dict, path: list[str], default):
    """Return the value at `path`, creating objects (and `default` at the leaf) as needed."""
    for index, key in enumerate(path):
        leaf = index == len(path) - 1
        expected = type(default) if leaf else dict
        if not isinstance(root.get(key), expected):
            root[key] = type(default)() if leaf else {}
        root = root[key]
    return root


def add_hook(partial: dict, event: str, pattern: str, hook: dict) -> None:
    matchers = container(partial, ["hooks", event], [])
    matcher = next((m for m in matchers if m.get("matcher", "") == pattern), None)
    if matcher is None:
        matcher = {"matcher": pattern, "hooks": []}
        matchers.append(matcher)
    matcher["hooks"].append(hook)


def main():
    if not SETTINGS.exists():
        sys.exit(f"Error: {SETTINGS} not found.")
    live = json.loads(SETTINGS.read_text())
    # The partial was removed pending a rewrite; adopting recreates it.
    partial = json.loads(PARTIAL.read_text()) if PARTIAL.exists() else {}
    overlay = json.loads(OVERLAY.read_text()) if OVERLAY.exists() else {}
    ignored = json.loads(IGNORE.read_text()) if IGNORE.exists() else []
    known = merge_local.combine(partial, overlay)
    candidates = [c for c in find_candidates(known, live) if c[0] not in ignored]
    if not candidates:
        print("No new items to review.")
        return
    print(f"Found {len(candidates)} item(s) to review.\n")
    adopted, localized, new_ignores = 0, 0, []
    for index, (key, heading, body, apply) in enumerate(candidates, 1):
        print(f"\n── [{index}/{len(candidates)}] {heading}")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        answer = ""
        while True:
            try:
                answer = (
                    input("[a]dopt / [l]ocal / [s]kip / [i]gnore / [q]uit > ")
                    .strip()
                    .lower()[:1]
                )
            except EOFError:
                answer = "q"
            if answer in ("a", "l", "s", "i", "q", ""):
                break
            print("  (use a/l/s/i/q)")
        if answer == "q":
            break
        if answer == "a":
            apply(partial)
            adopted += 1
        elif answer == "l":
            apply(overlay)
            localized += 1
        elif answer == "i":
            new_ignores.append(key)
    if adopted:
        PARTIAL.write_text(json.dumps(partial, indent=2, ensure_ascii=False) + "\n")
        print(f"\nAdopted {adopted} item(s) into {PARTIAL}")
    if localized:
        OVERLAY.parent.mkdir(parents=True, exist_ok=True)
        OVERLAY.write_text(json.dumps(overlay, indent=2, ensure_ascii=False) + "\n")
        print(f"\nKept {localized} item(s) for this machine in {OVERLAY}")
    if new_ignores:
        IGNORE.write_text(
            json.dumps(sorted({*ignored, *new_ignores}), indent=2, ensure_ascii=False)
            + "\n"
        )
        print(f"Added {len(new_ignores)} path(s) to {IGNORE}")
    if not adopted and not localized and not new_ignores:
        print("\nNo changes written.")


if __name__ == "__main__":
    main()
