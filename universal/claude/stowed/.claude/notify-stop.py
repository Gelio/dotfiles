#!/usr/bin/env python3
"""Claude Code Stop hook — desktop notification with sound when ready for input (macOS/WSL)."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from notify_utils import describe_session, notify, remove


def main():
    data = json.load(sys.stdin)
    cwd = data.get("cwd", "")

    # Dismiss any lingering permission notification (e.g. after denial)
    remove(f"claude-permission-{cwd}")

    title, subtitle = describe_session(cwd)
    message = "Ready for input"

    notify(title, subtitle, message, kind="stop",
           group=f"claude-stop-{cwd}", dismiss_after=5)


if __name__ == "__main__":
    main()
