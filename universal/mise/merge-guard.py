#!/usr/bin/env python3
"""Refuse a dotfiles apply that would discard live values of `merge` entries.

A merge entry sets the keys of its source in the target. Arrays are replaced
whole and scalars are overwritten, so anything added to them in the live file
(an agent's "always allow", a hand edit) would be lost. Lists each such value
and exits non-zero; adopt it into the source or delete it from the live file.
Set MISE_MERGE_ALLOW_LOSS=1 to apply anyway.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

LOADERS = {'.json': json.loads, '.toml': tomllib.loads}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def losses(source: object, live: object, path: str):
    """Yield a description of each live value the source would replace."""
    if isinstance(source, dict) and isinstance(live, dict):
        for key, value in source.items():
            if key in live:
                yield from losses(value, live[key], f'{path}.{key}' if path else key)
    elif isinstance(source, list) and isinstance(live, list):
        for item in live:
            if item not in source:
                yield f'{path}: drops {compact(item)}'
    elif source != live:
        yield f'{path}: replaces {compact(live)} with {compact(source)}'


def main() -> int:
    status = json.loads(subprocess.run(['mise', 'dot', 'status', '--json'], check=True, capture_output=True, text=True).stdout)
    found = False
    for edit in status.get('edits') or []:
        if not edit['edit'].startswith('merge:') or edit['state'] == 'applied':
            continue
        target = Path(edit['path']).expanduser()
        load = LOADERS.get(target.suffix)
        if load is None or not target.exists():
            continue
        try:
            live = load(target.read_text())
        except ValueError:
            continue  # mise refuses to write a target it can't parse
        source = load(Path(edit['origin']['source']).read_text())
        for loss in losses(source, live, ''):
            if not found:
                print('mise merge entries would discard live values:', file=sys.stderr)
                found = True
            print(f'  {edit["path"]} {loss}', file=sys.stderr)
    if not found:
        return 0
    if os.environ.get('MISE_MERGE_ALLOW_LOSS') == '1':
        print('MISE_MERGE_ALLOW_LOSS=1: applying anyway', file=sys.stderr)
        return 0
    print('Adopt them into the source or delete them from the live file, or re-run with MISE_MERGE_ALLOW_LOSS=1.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
