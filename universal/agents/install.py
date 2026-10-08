#!/usr/bin/env python3
"""Stow the shared agent resources into home; mise merges the settings."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


class Args(argparse.Namespace):
    """Typed `parse_args` result; argparse keeps these defaults when a flag is absent."""
    target_home: Path = Path.home()
    dry_run: bool = False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-home', type=Path, help='isolated installation target (default: current home)')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(namespace=Args())
    home = args.target_home.expanduser().resolve()
    # Shared resources belong to Stow. Settings, handoffs, and third-party skills do not.
    if not args.dry_run:
        for directory in ['.agents/skills', '.agents/lib', '.claude/skills', '.claude/hooks', '.codex/hooks', '.local/bin', '.local/agent-handoffs']:
            (home / directory).mkdir(parents=True, exist_ok=True)
    if not home.is_dir():
        parser.error('target home must exist for a dry run')
    stow = ['stow', '-R', '-d', str(ROOT), '-t', str(home), 'stowed']
    # Detect unmanaged conflicts before changing any links.
    subprocess.run([*stow, '--simulate'], check=True)
    if not args.dry_run:
        subprocess.run(stow, check=True)
    print(f'{"Would install" if args.dry_run else "Installed"}: shared resources in {home}')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
