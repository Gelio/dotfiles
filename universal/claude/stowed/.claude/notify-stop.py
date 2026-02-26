#!/usr/bin/env python3
"""Claude Code Stop hook — macOS notification with sound when ready for input."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from notify_utils import auto_dismiss, is_session_visible


def main():
    data = json.load(sys.stdin)
    cwd = data.get("cwd", "")

    # Dismiss any lingering permission notification (e.g. after denial)
    subprocess.run(
        [
            "terminal-notifier",
            "-remove", f"claude-permission-{cwd}",
        ]
    )

    if is_session_visible():
        return
    project = cwd.split("/")[-1] if cwd else "unknown"

    title = f"Claude Code — {project}"
    subtitle = cwd
    message = "Ready for input"

    group = f"claude-stop-{cwd}"
    subprocess.run(
        [
            "terminal-notifier",
            "-title", title,
            "-subtitle", subtitle,
            "-message", message,
            "-sound", "Glass",
            "-group", group,
        ]
    )
    auto_dismiss(group, delay_seconds=5)


if __name__ == "__main__":
    main()
