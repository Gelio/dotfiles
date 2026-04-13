#!/usr/bin/env python3
"""PostToolUse hook: advisory check for fixup commit scope.

After a Bash command completes, checks if a fixup commit was just created.
If so, compares the fixup's changed files against the target commit's files.
Warns (without blocking) if the fixup touches files not in the target commit.

This is advisory only — the agent decides whether to split the commit.
"""

import json
import shlex
import subprocess
import sys


def parse_input():
    data = json.load(sys.stdin)
    return data.get("tool_name", ""), data.get("tool_input", {})


def advisory(message: str):
    """Output advisory context — shown to the agent but does not block."""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": message,
                }
            }
        )
    )
    sys.exit(0)


def silent():
    sys.exit(0)


def run_git(*args: str) -> str:
    """Run a git command and return stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git", *args], capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def is_commit_command(command: str) -> bool:
    """Quick check — exit fast for the vast majority of Bash commands."""
    return "git" in command and "commit" in command


def extract_fixup_target_from_command(command: str) -> str | None:
    """Extract the --fixup target ref from the command string."""
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()

    for i, part in enumerate(parts):
        if part.startswith("--fixup="):
            ref = part.split("=", 1)[1]
        elif part == "--fixup" and i + 1 < len(parts):
            ref = parts[i + 1]
        else:
            continue
        # Strip amend:/reword: prefixes (git 2.32+)
        for prefix in ("amend:", "reword:"):
            if ref.startswith(prefix):
                ref = ref[len(prefix):]
        return ref

    return None


def find_target_by_subject(fixup_subject: str) -> str | None:
    """Find the target commit SHA by matching the subject line."""
    merge_base = run_git("merge-base", "HEAD", "main") or run_git(
        "merge-base", "HEAD", "master"
    )
    if not merge_base:
        return None

    # Search branch commits, excluding HEAD (the fixup itself)
    log_output = run_git("log", "--format=%H %s", f"{merge_base}..HEAD~1")
    if not log_output:
        return None

    for line in log_output.splitlines():
        sha, _, subject = line.partition(" ")
        if subject.startswith("fixup! "):
            continue  # skip other fixups
        if subject == fixup_subject:
            return sha

    return None


def main():
    tool_name, tool_input = parse_input()

    if tool_name != "Bash":
        silent()

    command = tool_input.get("command", "")
    if not is_commit_command(command):
        silent()

    # --- Is HEAD a fixup commit? ---
    head_subject = run_git("log", "-1", "--format=%s", "HEAD")
    if not head_subject or not head_subject.startswith("fixup! "):
        silent()

    # --- Find the target commit ---
    target_sha = None

    # Method 1: --fixup=<ref> in the command
    target_ref = extract_fixup_target_from_command(command)
    if target_ref:
        target_sha = run_git("rev-parse", target_ref)

    # Method 2: match by subject
    if not target_sha:
        target_subject = head_subject.removeprefix("fixup! ")
        target_sha = find_target_by_subject(target_subject)

    if not target_sha:
        silent()

    # --- Compare file sets ---
    target_files = set(
        filter(
            None,
            run_git(
                "diff-tree", "--no-commit-id", "-r", "--name-only", target_sha
            ).splitlines(),
        )
    )
    fixup_files = set(
        filter(
            None,
            run_git(
                "diff-tree", "--no-commit-id", "-r", "--name-only", "HEAD"
            ).splitlines(),
        )
    )

    if not fixup_files or not target_files:
        silent()

    extra_files = sorted(fixup_files - target_files)
    if not extra_files:
        silent()

    # --- Build advisory warning ---
    target_oneline = run_git("log", "--oneline", "-1", target_sha)

    warning = "\n".join(
        [
            "FIXUP SCOPE WARNING (advisory — not blocking)",
            f"  Target commit: {target_oneline}",
            f"  Target's files: {', '.join(sorted(target_files))}",
            f"  Extra files in this fixup: {', '.join(extra_files)}",
            "",
            "These extra files were not changed by the target commit. They may",
            "need separate fixup commits targeting the commits that introduced",
            "them. Check with:",
            "  git log --oneline $(git merge-base HEAD main)..HEAD -- <file>",
            "",
            "If these extra files are intentional (the fix genuinely requires",
            "touching files the original commit didn't), ignore this warning.",
        ]
    )

    advisory(warning)


if __name__ == "__main__":
    main()
