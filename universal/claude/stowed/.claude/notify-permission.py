#!/usr/bin/env python3
"""Claude Code PermissionRequest hook — macOS notification with sound."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from notify_utils import auto_dismiss, is_session_visible


def main():
    data = json.load(sys.stdin)

    if is_session_visible():
        return
    cwd = data.get("cwd", "")
    project = cwd.split("/")[-1] if cwd else "unknown"
    tool = data.get("tool_name", "unknown")
    tool_input = data.get("tool_input", {})

    # Build a short detail string depending on the tool
    detail = ""
    if tool == "Bash":
        cmd = tool_input.get("command", "")
        if cmd:
            detail = cmd[:100]
    elif tool in ("Edit", "Write"):
        path = tool_input.get("file_path", "")
        if path:
            detail = path.replace(cwd + "/", "") if cwd else path
    elif tool == "Read":
        path = tool_input.get("file_path", "")
        if path:
            detail = path.replace(cwd + "/", "") if cwd else path

    title = f"Claude Code — {project}"
    subtitle = cwd
    message = f"Permission needed: {tool}"
    if detail:
        message += f" — {detail}"

    group = f"claude-permission-{cwd}"
    subprocess.run(
        [
            "terminal-notifier",
            "-title", title,
            "-subtitle", subtitle,
            "-message", message,
            "-sound", "Funk",
            "-group", group,
        ]
    )
    auto_dismiss(group, delay_seconds=10)


if __name__ == "__main__":
    main()
