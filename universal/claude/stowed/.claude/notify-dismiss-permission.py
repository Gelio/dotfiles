#!/usr/bin/env python3
"""Claude Code PostToolUse hook — dismiss permission notification after tool executes."""

import json
import subprocess
import sys


def main():
    data = json.load(sys.stdin)
    cwd = data.get("cwd", "")

    subprocess.run(
        [
            "terminal-notifier",
            "-remove", f"claude-permission-{cwd}",
        ]
    )


if __name__ == "__main__":
    main()
