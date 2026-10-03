#!/usr/bin/env python3
"""Install shared resources and merge only the selected agents' settings."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=['claude', 'codex', 'both'], default='claude')
    parser.add_argument('--target-home', type=Path, default=Path.home(), help='isolated installation target (default: current home)')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    home = args.target_home.expanduser().resolve()
    # Shared resources belong to Stow. Settings and third-party skills do not.
    if not args.dry_run:
        for directory in ['.agents/skills', '.agents/lib', '.claude/skills', '.claude/hooks', '.codex/hooks', '.local/bin']:
            (home / directory).mkdir(parents=True, exist_ok=True)
    if not home.is_dir():
        parser.error('target home must exist for a dry run')
    stow = ['stow', '-R', '-d', str(ROOT), '-t', str(home), 'stowed']
    # Detect unmanaged conflicts before changing any links or settings.
    subprocess.run([*stow, '--simulate'], check=True)
    agents = ['claude', 'codex'] if args.agent == 'both' else [args.agent]
    for agent in agents:
        settings = home / f'.{agent}' / ('settings.json' if agent == 'claude' else 'hooks.json')
        if settings.exists():
            if not isinstance(json.loads(settings.read_text()), dict):
                parser.error(f'Settings must contain a JSON object: {settings}')
    migration = ['python3', str(ROOT / 'migrate-handoff-storage.py'), '--target-home', str(home)]
    subprocess.run([*migration, '--dry-run'], check=True)
    if not args.dry_run:
        subprocess.run(migration, check=True)
        subprocess.run(stow, check=True)
        for agent in agents:
            subprocess.run(['node', '--experimental-strip-types', str(ROOT / 'setup-settings.ts'),
                            '--agent', agent, '--target-home', str(home)], check=True)
    print(f'{"Would install" if args.dry_run else "Installed"}: shared resources + {", ".join(agents)} settings in {home}')
    if 'codex' in agents:
        print('Restart Codex and review/trust the hook definitions when prompted.')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
