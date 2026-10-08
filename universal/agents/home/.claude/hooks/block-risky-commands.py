#!/usr/bin/env python3
"""Claude adapter; retain the existing hook path and sandbox exception."""
import json
import re
import shlex
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".agents/lib"))
from agent_setup.commands import check_command, get_parts

def check_playwright_sandbox(command: str, tool_input: dict) -> str | None:
    """Playwright e2e tests need sandbox disabled to launch Chromium."""
    parts = get_parts(command)
    has_npx_playwright = any(
        parts[i] == "npx" and parts[i + 1] == "playwright"
        for i in range(len(parts) - 1)
    )
    is_playwright = has_npx_playwright or any(
        kw in parts
        for kw in ("test:e2e", "test:e2e:chrome", "test:e2e:firefox")
    )
    if not is_playwright:
        return None
    if tool_input.get("dangerouslyDisableSandbox"):
        return None
    return (
        "Playwright e2e tests must run with dangerouslyDisableSandbox: true. "
        "Chromium needs Mach port access that the sandbox blocks."
    )


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    args = data.get("tool_input", {})
    command = args.get("command", "")
    reason = check_command(command)
    if not reason:
        for segment in re.split(r'\s*(?:&&|\|\||;)\s*', command):
            reason = check_playwright_sandbox(segment, args)
            if reason:
                break
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))

if __name__ == "__main__":
    main()
