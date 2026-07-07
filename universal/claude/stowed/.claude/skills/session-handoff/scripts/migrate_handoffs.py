#!/usr/bin/env python3
"""Migrate repo-local handoffs into the centralized store.

Older handoffs lived inside each repository at `<repo>/.claude/handoffs/`.
Handoffs are now stored centrally at `~/.local/claude-handoffs/<repo-key>/` (see
_handoff_paths.py for why). This script moves any repo-local handoffs into the
centralized location for one or more repositories.

Usage:
    python migrate_handoffs.py                 # migrate the current session's repo
    python migrate_handoffs.py /path/to/repo   # migrate specific repo(s)
    python migrate_handoffs.py ~/a ~/b ...      # several at once
    python migrate_handoffs.py --dry-run [...]  # preview without moving

For each repo, source files at `<repo-root>/.claude/handoffs/*.md` are moved to
`~/.local/claude-handoffs/<repo-key>/`. A file whose name already exists at the
destination is left in place and reported (never overwritten). An emptied
source directory is removed.
"""

import argparse
import shutil
import sys
from pathlib import Path

# Allow importing the shared resolver whether run directly or via a symlink.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ._handoff_paths import handoffs_dir, repo_key, resolve_project_root


def migrate_repo(repo_arg: str | None, dry_run: bool) -> tuple[int, int]:
    """Migrate one repo. Returns (moved, skipped)."""
    repo_root = resolve_project_root(repo_arg)
    src = Path(repo_root) / ".claude" / "handoffs"
    dst = handoffs_dir(repo_root)

    if not src.exists() or not src.is_dir():
        print(f"[skip] {repo_root}")
        print(f"       no repo-local handoffs at {src}")
        return (0, 0)

    sources = sorted(src.glob("*.md"))
    if not sources:
        print(f"[skip] {repo_root}: {src} has no *.md handoffs")
        return (0, 0)

    print(f"[repo] {repo_root}")
    print(f"       key: {repo_key(repo_root)}")
    print(f"       {src}  ->  {dst}")

    moved = skipped = 0
    if not dry_run:
        dst.mkdir(parents=True, exist_ok=True)

    for f in sources:
        target = dst / f.name
        if target.exists():
            print(f"       [skip] {f.name} (already at destination)")
            skipped += 1
            continue
        if dry_run:
            print(f"       [would move] {f.name}")
        else:
            shutil.move(str(f), str(target))
            print(f"       [moved] {f.name}")
        moved += 1

    # Remove the source dir if it is now empty (don't touch a non-empty one).
    if not dry_run and not any(src.iterdir()):
        try:
            src.rmdir()
            print(f"       [removed empty] {src}")
        except OSError:
            pass

    return (moved, skipped)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate repo-local handoffs into the centralized store"
    )
    parser.add_argument(
        "repos",
        nargs="*",
        help="Repo path(s) to migrate (default: the current session's repo)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would move without moving anything",
    )
    args = parser.parse_args()

    targets = args.repos if args.repos else [None]

    total_moved = total_skipped = 0
    for repo in targets:
        moved, skipped = migrate_repo(repo, args.dry_run)
        total_moved += moved
        total_skipped += skipped
        print()

    verb = "would move" if args.dry_run else "moved"
    print(f"Done: {verb} {total_moved} handoff(s), skipped {total_skipped}.")


if __name__ == "__main__":
    main()
