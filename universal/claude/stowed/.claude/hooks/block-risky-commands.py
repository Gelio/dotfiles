#!/usr/bin/env python3
"""PreToolUse hook: block risky/destructive commands.

Blocks commands that are hard to reverse or affect shared state:
- git push (any variant)
- git reset --hard
- git checkout -- (discard changes)
- git clean -f
- git branch -D (force delete)
- rm -rf
- gh pr merge / close
- gh issue close
- gh release create / delete
"""

import json
import shlex
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


def get_parts(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def find_git_subcommand(parts: list[str]) -> tuple[int, str | None]:
    """Find the git subcommand, skipping git-level flags like -c key=value."""
    i = 0
    while i < len(parts) and parts[i] != "git":
        i += 1
    if i >= len(parts):
        return -1, None
    i += 1  # skip 'git'
    while i < len(parts):
        if parts[i] in ("-c", "--config", "-C"):
            i += 2
        elif parts[i].startswith("-"):
            i += 1
        else:
            break
    if i >= len(parts):
        return -1, None
    return i, parts[i]


RISKY_PATTERNS = [
    {
        "check": lambda parts, sub_idx, sub: sub == "push",
        "msg": "git push is blocked. Push manually after reviewing changes.",
    },
    {
        "check": lambda parts, sub_idx, sub: (
            sub == "reset" and "--hard" in parts[sub_idx:]
        ),
        "msg": "git reset --hard is blocked — it discards uncommitted work.",
    },
    {
        "check": lambda parts, sub_idx, sub: (
            sub == "checkout" and "--" in parts[sub_idx:]
        ),
        "msg": "git checkout -- is blocked — it discards uncommitted changes to files.",
    },
    {
        "check": lambda parts, sub_idx, sub: (
            sub == "restore" and "--staged" not in parts[sub_idx:]
        ),
        "msg": "git restore (without --staged) is blocked — it discards uncommitted changes.",
    },
    {
        "check": lambda parts, sub_idx, sub: (
            sub == "clean" and any(f.startswith("-") and "f" in f for f in parts[sub_idx + 1:])
        ),
        "msg": "git clean -f is blocked — it deletes untracked files permanently.",
    },
    {
        "check": lambda parts, sub_idx, sub: (
            sub == "branch" and any(f in ("-D", "--delete-force") for f in parts[sub_idx + 1:])
        ),
        "msg": "git branch -D is blocked — use -d for safe deletion instead.",
    },
]


def check_risky_git(command: str) -> str | None:
    parts = get_parts(command)
    sub_idx, sub = find_git_subcommand(parts)
    if sub is None:
        return None
    for pattern in RISKY_PATTERNS:
        if pattern["check"](parts, sub_idx, sub):
            return pattern["msg"]
    return None


RISKY_GH_PATTERNS = [
    {
        "check": lambda parts: "pr" in parts and "merge" in parts,
        "msg": "gh pr merge is blocked — merge PRs manually after review.",
    },
    {
        "check": lambda parts: "pr" in parts and "close" in parts,
        "msg": "gh pr close is blocked — close PRs manually.",
    },
    {
        "check": lambda parts: "issue" in parts and "close" in parts,
        "msg": "gh issue close is blocked — close issues manually.",
    },
    {
        "check": lambda parts: "release" in parts and "create" in parts,
        "msg": "gh release create is blocked — create releases manually.",
    },
    {
        "check": lambda parts: "release" in parts and "delete" in parts,
        "msg": "gh release delete is blocked — delete releases manually.",
    },
]


def check_risky_gh(command: str) -> str | None:
    parts = get_parts(command)
    if not parts or parts[0] != "gh":
        return None
    for pattern in RISKY_GH_PATTERNS:
        if pattern["check"](parts):
            return pattern["msg"]
    return None


def check_rm_rf(command: str) -> str | None:
    parts = get_parts(command)
    for i, p in enumerate(parts):
        if p == "rm":
            flags_after = parts[i + 1:]
            for f in flags_after:
                if f.startswith("-") and "r" in f and "f" in f:
                    return "rm -rf is blocked — too risky for automated execution."
                if f == "--":
                    break
            break
    return None


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
    tool_name, tool_input = parse_input()

    if tool_name != "Bash":
        approve()

    command = tool_input.get("command", "")

    # Check for chained commands — split on &&, ||, ;, |
    # Simple split: check each segment
    import re
    segments = re.split(r'\s*(?:&&|\|\||;)\s*', command)

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        reason = check_risky_git(segment)
        if reason:
            block(reason)

        reason = check_risky_gh(segment)
        if reason:
            block(reason)

        reason = check_rm_rf(segment)
        if reason:
            block(reason)

        reason = check_playwright_sandbox(segment, tool_input)
        if reason:
            block(reason)

    approve()


if __name__ == "__main__":
    main()
