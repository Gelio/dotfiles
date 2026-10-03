#!/usr/bin/env python3
"""Claude adapter for the advisory fixup-scope check."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".agents/lib"))
from agent_setup.fixups import check_fixup

def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    warning = check_fixup(data.get("tool_input", {}).get("command", ""), data.get("cwd"))
    if warning:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": warning}}))

if __name__ == "__main__":
    main()
