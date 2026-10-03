#!/usr/bin/env python3
"""Claude Code PermissionRequest hook — desktop notification with sound (macOS/WSL)."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from notify_utils import describe_session, notify, shorten_path


def main():
    data = json.load(sys.stdin)
    cwd = data.get("cwd", "")
    tool = data.get("tool_name", "unknown")
    tool_input = data.get("tool_input", {})

    # Build a short detail string depending on the tool
    detail = ""
    if tool == "Bash":
        cmd = tool_input.get("command", "")
        if cmd:
            detail = shorten_path(cmd[:100])
    elif tool in ("Edit", "Write", "Read"):
        path = tool_input.get("file_path", "")
        if path:
            # Show relative to cwd, fall back to shortened absolute
            if cwd and path.startswith(cwd + "/"):
                detail = path[len(cwd) + 1:]
            else:
                detail = shorten_path(path)

    title, subtitle = describe_session(cwd)
    message = f"Permission needed: {tool}"
    if detail:
        message += f" — {detail}"

    notify(title, subtitle, message, kind="permission",
           group=f"claude-permission-{cwd}", dismiss_after=10)


if __name__ == "__main__":
    main()
