#!/usr/bin/env python3
"""Claude Code PostToolUse hook — dismiss permission notification after tool executes."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from notify_utils import remove


def main():
    data = json.load(sys.stdin)
    remove(f"claude-permission-{data.get('cwd', '')}")


if __name__ == "__main__":
    main()
