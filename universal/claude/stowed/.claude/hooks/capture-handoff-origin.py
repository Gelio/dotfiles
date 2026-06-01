#!/usr/bin/env python3
"""SessionStart hook: record the session's origin git repository.

Handoffs must always be written into the git repository of the directory where
the Claude session was *started* -- never wherever the agent happens to have
`cd`'d to (multi-repo / multi-agent work). Run-time cwd is unreliable for this,
so we capture the origin once, at session start, when cwd is guaranteed to be
the launch directory.

We resolve the git toplevel of the launch directory and stash it in
~/.local/claude-handoffs/.origins/<session_id>. create_handoff.py (and
list_handoffs.py) read it back via $CLAUDE_CODE_SESSION_ID, so they always
target the right repo regardless of the current working directory.

This hook is best-effort: any failure exits 0 so it can never block a session.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def git_toplevel(path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    session_id = data.get("session_id") or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        sys.exit(0)

    # At SessionStart, the hook cwd / CLAUDE_PROJECT_DIR is the launch directory.
    launch_dir = (
        data.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )

    origin = git_toplevel(launch_dir) or launch_dir

    # Kept in sync with _handoff_paths.origins_dir(). NOT under ~/.claude/, which
    # would trigger Claude Code's "edit its own settings" prompt for tool writes.
    try:
        origins_dir = Path.home() / ".local" / "claude-handoffs" / ".origins"
        origins_dir.mkdir(parents=True, exist_ok=True)
        (origins_dir / session_id).write_text(origin + "\n")
    except OSError:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
