#!/usr/bin/env python3
"""Review ~/.claude/settings.json for items to adopt into settings-partial.json.

For each live value the partial doesn't already contribute, prompt:
  [a]dopt  - write the item into settings-partial.json
  [s]kip   - skip for this run (ask again next time)
  [i]gnore - add to .settings-review-ignore.json (never ask again)
  [q]uit   - stop reviewing and save what's been chosen so far

The mise merge entry replaces arrays whole, so adopt live-only items before
`mise dot apply` (mise/merge-guard.py lists them and stops the apply). Objects are walked per leaf, arrays are
diffed by value, and `hooks` is walked matcher by matcher and command by command.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SETTINGS = Path.home() / '.claude/settings.json'
PARTIAL = ROOT / 'settings-partial.json'
IGNORE = ROOT / '.settings-review-ignore.json'


def compact(value) -> str:
    """Match JSON.stringify so existing ignore keys stay valid."""
    return json.dumps(value, separators=(',', ':'), ensure_ascii=False)


def same_hook(a: dict, b: dict) -> bool:
    return (a.get('type'), a.get('command'), a.get('if')) == (b.get('type'), b.get('command'), b.get('if'))


def find_candidates(partial: dict, live: dict):
    """Yield (ignore key, heading, body, apply) for each item missing from the partial."""
    for key, value in live.items():
        if key == 'hooks':
            yield from hook_candidates(partial.get('hooks') or {}, value)
        else:
            yield from value_candidates([key], partial.get(key), value)


def value_candidates(path: list[str], partial, live):
    dotted = '.'.join(path)
    if isinstance(live, dict):
        for key, value in live.items():
            yield from value_candidates([*path, key], partial.get(key) if isinstance(partial, dict) else None, value)
    elif isinstance(live, list):
        existing = partial if isinstance(partial, list) else []
        for item in live:
            if item not in existing:
                yield f'{dotted}[]:{compact(item)}', f'Append to {dotted}', item, lambda p, i=item: container(p, path, []).append(i)
    elif compact(partial) != compact(live):
        def assign(p, value=live):
            container(p, path[:-1], {})[path[-1]] = value
        yield dotted, f'Set {dotted}', live, assign


def hook_candidates(partial: dict, live: dict):
    for event, matchers in live.items():
        for matcher in matchers:
            pattern = matcher.get('matcher', '')
            label = f'hooks.{event}[matcher={compact(pattern)}]'
            existing = next((m for m in partial.get(event, []) if m.get('matcher', '') == pattern), None)
            if existing is None:
                yield label, f'Add hook matcher  {label}', matcher, lambda p, e=event, m=matcher: container(p, ['hooks', e], []).append(m)
                continue
            for hook in matcher.get('hooks', []):
                if any(same_hook(h, hook) for h in existing['hooks']):
                    continue
                key = {k: hook[k] for k in ('type', 'command', 'if') if hook.get(k)}
                yield f'{label}.hooks:{compact(key)}', f'Add hook command  {label}', hook, lambda p, e=event, pat=pattern, h=hook: add_hook(p, e, pat, h)


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
    matchers = container(partial, ['hooks', event], [])
    matcher = next((m for m in matchers if m.get('matcher', '') == pattern), None)
    if matcher is None:
        matcher = {'matcher': pattern, 'hooks': []}
        matchers.append(matcher)
    matcher['hooks'].append(hook)


def main():
    if not SETTINGS.exists():
        sys.exit(f'Error: {SETTINGS} not found.')
    live = json.loads(SETTINGS.read_text())
    partial = json.loads(PARTIAL.read_text())
    ignored = json.loads(IGNORE.read_text()) if IGNORE.exists() else []
    candidates = [c for c in find_candidates(partial, live) if c[0] not in ignored]
    if not candidates:
        print('No new items to review.')
        return
    print(f'Found {len(candidates)} item(s) to review.\n')
    adopted, new_ignores = 0, []
    for index, (key, heading, body, apply) in enumerate(candidates, 1):
        print(f'\n── [{index}/{len(candidates)}] {heading}')
        print(json.dumps(body, indent=2, ensure_ascii=False))
        answer = ''
        while True:
            try:
                answer = input('[a]dopt / [s]kip / [i]gnore / [q]uit > ').strip().lower()[:1]
            except EOFError:
                answer = 'q'
            if answer in ('a', 's', 'i', 'q', ''):
                break
            print('  (use a/s/i/q)')
        if answer == 'q':
            break
        if answer == 'a':
            apply(partial)
            adopted += 1
        elif answer == 'i':
            new_ignores.append(key)
    if adopted:
        PARTIAL.write_text(json.dumps(partial, indent=2, ensure_ascii=False) + '\n')
        print(f'\nAdopted {adopted} item(s) into {PARTIAL}')
    if new_ignores:
        IGNORE.write_text(json.dumps(sorted({*ignored, *new_ignores}), indent=2, ensure_ascii=False) + '\n')
        print(f'Added {len(new_ignores)} path(s) to {IGNORE}')
    if not adopted and not new_ignores:
        print('\nNo changes written.')


if __name__ == '__main__':
    main()
