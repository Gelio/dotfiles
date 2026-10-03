#!/usr/bin/env python3
"""Claude adapter for shared commit policy, preserving Claude attribution."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".agents/lib"))
from agent_setup.commits import check_commit

def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    reason = check_commit(data.get("tool_input", {}).get("command", ""), data.get("cwd", ""), "claude")
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))

if __name__ == "__main__":
    main()
