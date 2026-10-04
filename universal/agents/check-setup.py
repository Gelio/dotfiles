#!/usr/bin/env python3
"""Check installed links and owned hook registrations without changing files."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent


def check(home: Path, agents: list[str]) -> list[str]:
    errors = []
    shared = ROOT / 'stowed/.agents/skills'
    for source in shared.iterdir():
        locations = [home / '.agents/skills' / source.name]
        if 'claude' in agents:
            locations.append(home / '.claude/skills' / source.name)
        for path in locations:
            if not path.exists() or path.resolve() != source.resolve():
                errors.append(f'Incorrect or missing authored skill link: {path}')
    for agent in agents:
        settings = home / f'.{agent}' / ('settings.json' if agent == 'claude' else 'hooks.json')
        partial = ROOT / ('settings-partial.json' if agent == 'claude' else 'codex-hooks-partial.json')
        try:
            data = json.loads(settings.read_text())
            for event, matchers in json.loads(partial.read_text())['hooks'].items():
                installed = data.get('hooks', {}).get(event, [])
                for matcher in matchers:
                    for hook in matcher['hooks']:
                        found = sum(h.get('command') == hook['command'] and h.get('type') == hook['type']
                                    for m in installed if m.get('matcher', '') == matcher.get('matcher', '')
                                    for h in m.get('hooks', []))
                        if found != 1:
                            errors.append(f'{agent} {event}: expected one registration of {hook["command"]}, found {found}')
            for event, matchers in data.get('hooks', {}).items():
                counts = Counter((m.get('matcher', ''), h.get('type'), h.get('command')) for m in matchers for h in m.get('hooks', []))
                for item, count in counts.items():
                    if count > 1:
                        errors.append(f'{agent} {event}: duplicate hook {item[2]}')
        except (OSError, ValueError, TypeError) as error:
            errors.append(f'Cannot inspect {settings}: {error}')
        for source in (ROOT / f'stowed/.{agent}/hooks').iterdir():
            if source.is_file():
                installed = home / f'.{agent}/hooks' / source.name
                if not installed.exists() or installed.resolve() != source.resolve():
                    errors.append(f'Incorrect or missing hook link: {installed}')
    old = home / '.local/claude-handoffs'
    new = home / '.local/agent-handoffs'
    if not new.is_dir():
        errors.append(f'Missing shared handoff store: {new}')
    if old.exists() and (not old.is_symlink() or old.resolve() != new.resolve()):
        errors.append(f'Legacy handoff store was not migrated: {old}')
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-home', type=Path, default=Path.home())
    parser.add_argument('--agent', choices=['claude', 'codex', 'both'], default='both')
    args = parser.parse_args()
    agents = ['claude', 'codex'] if args.agent == 'both' else [args.agent]
    errors = check(args.target_home.expanduser().resolve(), agents)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        sys.exit(1)
    print('Shared skill links, hook registrations, and handoff storage are valid.')
