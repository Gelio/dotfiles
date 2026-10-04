#!/usr/bin/env python3
"""Restore third-party skills recorded in the skills CLI's global lockfile."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='run the commands (default: print only)')
    parser.add_argument('--agent', nargs='+', choices=['claude-code', 'codex'], default=['claude-code', 'codex'])
    args = parser.parse_args()
    lock = json.loads((ROOT / 'stowed/.agents/.skill-lock.json').read_text())
    groups = defaultdict(list)
    for name, skill in lock['skills'].items():
        if skill['sourceType'] != 'github':
            parser.error(f'Unsupported source type for {name}: {skill["sourceType"]}')
        groups[skill['source']].append(name)
    print('Restores recorded selections from upstream; folder hashes are not revision pins.')
    for source, names in groups.items():
        command = ['npx', 'skills', 'add', source, '--skill', *names, '--agent', *args.agent, '--global', '--yes']
        print(shlex.join(command), flush=True)
        if args.apply:
            subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
