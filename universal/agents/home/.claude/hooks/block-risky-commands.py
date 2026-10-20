#!/usr/bin/env python3
"""Claude adapter; retain the existing hook path and sandbox exception."""
import json
import re
import shlex
import subprocess
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


def _settings_files(cwd: str | None) -> list[Path]:
    """Settings in increasing precedence: user, project, local, managed."""
    files = [Path.home() / ".claude/settings.json"]
    if cwd:
        project = Path(cwd)
        toplevel = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                                  capture_output=True, text=True).stdout.strip()
        for root in dict.fromkeys(p for p in (Path(toplevel) if toplevel else None, project) if p):
            files += [root / ".claude/settings.json", root / ".claude/settings.local.json"]
    files.append(Path("/etc/claude-code/managed-settings.json"))
    return files


def sandbox_covers_rm(cwd: str | None) -> bool:
    """Whether rm runs sandboxed: the sandbox is enabled and rm isn't excluded."""
    enabled = False
    excluded: list[str] = []
    for path in _settings_files(cwd):
        try:
            sandbox = json.loads(path.read_text()).get("sandbox", {})
        except (OSError, ValueError, AttributeError):
            continue
        if "enabled" in sandbox:
            enabled = bool(sandbox["enabled"])
        excluded += sandbox.get("excludedCommands", [])
    return enabled and not any(e.split()[0] in ("rm", "*") for e in excluded if e.split())


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    args = data.get("tool_input", {})
    command = args.get("command", "")
    sandboxed = not args.get("dangerouslyDisableSandbox") and sandbox_covers_rm(data.get("cwd"))
    reason = check_command(command, data.get("cwd"), sandboxed)
    if not reason:
        for segment in re.split(r'\s*(?:&&|\|\||;)\s*', command):
            reason = check_playwright_sandbox(segment, args)
            if reason:
                break
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # a crashing hook would let the command through
        print(json.dumps({"decision": "block",
                          "reason": f"block-risky-commands hook failed ({e!r}); command blocked."}))
