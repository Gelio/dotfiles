#!/usr/bin/env python3
"""Move the Claude handoff store to the shared location; preserve old paths."""
import argparse
from datetime import datetime
from pathlib import Path
import shutil


def migrate(home: Path, dry_run: bool = False):
    old = home / '.local/claude-handoffs'
    new = home / '.local/agent-handoffs'
    if old.is_symlink():
        if old.resolve() != new.resolve():
            raise RuntimeError(f'Refusing unexpected legacy symlink: {old}')
        return
    if not old.exists():
        if not dry_run:
            new.mkdir(parents=True, exist_ok=True)
        return
    if not old.is_dir() or (new.exists() and not new.is_dir()):
        raise RuntimeError('Handoff stores must be directories')
    if new.is_symlink():
        raise RuntimeError(f'Refusing symlink destination: {new}')
    # Validate all conflicts before moving anything. Preserve equal duplicates
    # in a legacy backup when both stores already exist.
    for source in old.rglob('*'):
        target = new / source.relative_to(old)
        if source.is_symlink():
            raise RuntimeError(f'Refusing symlink inside legacy store: {source}')
        if target.exists():
            if source.is_dir() != target.is_dir() or (source.is_file() and source.read_bytes() != target.read_bytes()):
                raise RuntimeError(f'Handoff storage conflict: {target}')
    print(f'{"Would migrate" if dry_run else "Migrating"} {old} -> {new}')
    if dry_run:
        return
    if not new.exists():
        old.rename(new)
    else:
        for source in old.rglob('*'):
            target = new / source.relative_to(old)
            if source.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        backup = old.with_name(f'{old.name}.backup-{datetime.now().strftime("%Y%m%d-%H%M%S-%f")}')
        old.rename(backup)
        print(f'Legacy backup: {backup}')
    # Relative link also keeps existing handoff-chain references and running
    # Claude sessions valid; both names now refer to one store.
    old.symlink_to('agent-handoffs', target_is_directory=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-home', type=Path, default=Path.home())
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    migrate(args.target_home.expanduser().resolve(), args.dry_run)
