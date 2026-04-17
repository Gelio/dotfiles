#!/usr/bin/env python3
"""PreToolUse hook: ensure create_handoff.py runs from the git repo root.

The create_handoff.py script uses os.getcwd() to determine where to place
.claude/handoffs/. If the working directory is a subdirectory (e.g.
onprem/ui), handoffs end up in the wrong location. This hook blocks the
command and tells the agent to cd to the git root first.
"""

import json
import os
import subprocess
import sys


def parse_input():
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    return tool_name, tool_input


def block(reason: str):
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def approve():
    sys.exit(0)


def get_git_toplevel() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def main():
    tool_name, tool_input = parse_input()

    if tool_name != "Bash":
        approve()

    command = tool_input.get("command", "")

    if "create_handoff.py" not in command:
        approve()

    cwd = os.getcwd()
    git_root = get_git_toplevel()

    if git_root and os.path.realpath(cwd) != os.path.realpath(git_root):
        block(
            f"create_handoff.py must run from the git repo root.\n"
            f"  Current directory: {cwd}\n"
            f"  Git root:          {git_root}\n"
            f"Fix: prefix the command with `cd {git_root} && `"
        )

    approve()


if __name__ == "__main__":
    main()
