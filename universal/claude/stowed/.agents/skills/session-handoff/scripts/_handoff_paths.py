#!/usr/bin/env python3
"""Shared helper: resolve the project root for handoff storage.

Handoffs must always live in the git repository of the directory where the
Claude session was STARTED, regardless of any `cd` the agent performs during
the session (multi-repo / multi-agent work). Run-time cwd is therefore NOT
trusted as the primary source.

Resolution order:
  1. An explicit directory passed by the caller (e.g. --project-dir).
  2. The session-origin file captured at SessionStart by
     capture-handoff-origin.py (~/.local/claude-handoffs/.origins/<session_id>).
     This already holds the resolved git toplevel of the launch directory and
     is immune to any later `cd`.
  3. $CLAUDE_PROJECT_DIR (the launch dir, when present), resolved to its git
     toplevel.
  4. The current working directory, resolved to its git toplevel.
  5. The current working directory verbatim (non-git fallback).
"""

import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Handoff:
    path: str
    filename: str
    title: str
    date: datetime | None
    status: str = ""
    size: int = 0


def git_toplevel(path: str) -> str | None:
    """Return the git repository root containing `path`, or None."""
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def session_origin() -> str | None:
    """Return the git root captured for this session at SessionStart, if any."""
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        return None
    origin_file = origins_dir() / session_id
    try:
        if origin_file.is_file():
            value = origin_file.read_text().strip()
            return value or None
    except OSError:
        pass
    return None


def resolve_project_root(explicit: str | None = None) -> str:
    """Resolve where handoffs should live for the current session."""
    # 1. Explicit override (resolved to its git root when possible).
    if explicit:
        return git_toplevel(explicit) or explicit

    # 2. Origin captured at SessionStart -- already a git root, cd-immune.
    origin = session_origin()
    if origin:
        return origin

    # 3. Launch dir from the environment -> its git root.
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_dir:
        return git_toplevel(env_dir) or env_dir

    # 4 / 5. Fall back to the current working directory's git root, then cwd.
    cwd = os.getcwd()
    return git_toplevel(cwd) or cwd


def handoffs_root() -> Path:
    """The single, centralized location for all handoffs across repos.

    Handoffs are NOT stored inside each repo (a repo-local `.claude/handoffs/`
    can sit above the launch directory, which the OS command sandbox -- which
    only honors concrete writable paths, not globs -- then refuses to write to).
    A single fixed root sidesteps that: it is added once to
    `sandbox.filesystem.allowWrite` and is writable from any working directory.

    NOT under `~/.claude/`: Claude Code treats every write beneath `~/.claude/`
    as a potential settings edit and raises an "allow Claude to edit its own
    settings" prompt that no permission rule can suppress. `~/.local/` avoids it.
    """
    return Path.home() / ".local" / "claude-handoffs"


def origins_dir() -> Path:
    """Where SessionStart stashes each session's resolved origin git root."""
    return handoffs_root() / ".origins"


def repo_key(project_root: str) -> str:
    """Encode a repo path into a flat directory name.

    Mirrors Claude Code's own project-dir encoding (path separators -> '-'),
    e.g. /Users/me/ubuntu-dotfiles -> -Users-me-ubuntu-dotfiles. The real path
    is also recorded in each handoff's `Project:` metadata, so this only needs
    to be a stable, collision-free key per repo.
    """
    resolved = os.path.abspath(os.path.expanduser(project_root))
    return resolved.replace(os.sep, "-")


def handoffs_dir(project_root: str) -> Path:
    """The centralized handoffs directory for a given repo root."""
    return handoffs_root() / repo_key(project_root)
