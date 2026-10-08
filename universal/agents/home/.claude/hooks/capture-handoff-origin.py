#!/usr/bin/env python3
"""Claude SessionStart adapter; best-effort capture of the launch repository."""
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".agents/skills/session-handoff/scripts"))
from _handoff_paths import capture_origin


def main():
    try:
        data = json.load(sys.stdin)
        data.setdefault("session_id", os.environ.get("CLAUDE_CODE_SESSION_ID"))
        data.setdefault("cwd", os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        capture_origin(data, "claude")
    except (OSError, ValueError, TypeError):
        pass  # Capturing an origin must never prevent Claude from starting.

if __name__ == "__main__":
    main()
