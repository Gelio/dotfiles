#!/usr/bin/env python3
"""PreToolUse hook: validate git commit conventions.

Ensures:
1. git commit uses -F (not -m) for the commit message
2. The commit message file exists and follows formatting rules:
   - Subject line: <type>(<scope>): <subject>, max 72 chars, no trailing period
   - Blank line after subject
   - Body present, lines wrapped at 72 chars
   - Co-Authored-By trailer present with correct format
   - One idea per paragraph (no overly long paragraphs)
"""

import json
import re
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
    # No output = approve
    sys.exit(0)


def _is_git_commit_parts(parts: list[str]) -> bool:
    """Check if a list of tokens represents a git commit command."""
    if not parts or (parts[0] != "git" and not parts[0].endswith("/git")):
        return False
    i = 1  # skip 'git'
    # Skip git-level options before the subcommand
    while i < len(parts):
        if parts[i] in ("-c", "--config"):
            i += 2  # skip flag and its value
        elif parts[i].startswith("-"):
            i += 1
        else:
            break
    return i < len(parts) and parts[i] == "commit"


def find_git_commit_command(command: str) -> str | None:
    """Find the git commit sub-command in a possibly chained command.

    Handles shell operators (&&, ||, ;, |) so that e.g.
    'git add file && git commit --fixup abc' correctly finds the commit.
    Returns the sub-command string if found, None otherwise.
    """
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()

    # Split tokens into sub-commands at shell operators
    subcommands: list[list[str]] = []
    current: list[str] = []
    for part in parts:
        if part in ("&&", "||", ";", "|"):
            if current:
                subcommands.append(current)
            current = []
        else:
            current.append(part)
    if current:
        subcommands.append(current)

    for subcmd in subcommands:
        if _is_git_commit_parts(subcmd):
            return shlex.join(subcmd)
    return None


def extract_flag_value(command: str, flag: str) -> str | None:
    """Extract value for a flag like -F or --file from command."""
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    for i, p in enumerate(parts):
        if p == flag and i + 1 < len(parts):
            return parts[i + 1]
        if p.startswith(f"{flag}="):
            return p.split("=", 1)[1]
    return None


def has_flag(command: str, *flags: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    return any(p in flags for p in parts)


VALID_TYPES = {
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert",
}

SUBJECT_RE = re.compile(
    r"^(?:fixup! )?(\w+)(?:\(([^)]+)\))?!?: .+$"
)


def validate_commit_message(filepath: str) -> list[str]:
    """Validate commit message file and return list of issues."""
    try:
        with open(filepath) as f:
            content = f.read()
    except FileNotFoundError:
        return [f"Commit message file not found: {filepath}"]
    except OSError as e:
        return [f"Cannot read commit message file: {e}"]

    lines = content.rstrip("\n").split("\n")
    issues = []

    if not lines or not lines[0].strip():
        return ["Commit message is empty"]

    # --- Subject line ---
    subject = lines[0]

    if len(subject) > 72:
        issues.append(
            f"Subject line is {len(subject)} chars (max 72): {subject!r}"
        )

    if subject.endswith("."):
        issues.append("Subject line should not end with a period")

    match = SUBJECT_RE.match(subject)
    if not match:
        issues.append(
            f"Subject doesn't match `<type>(<scope>): <subject>` format: {subject!r}"
        )
    else:
        commit_type = match.group(1)
        # For fixup! commits, the type is the one after the prefix
        actual_type = subject.removeprefix("fixup! ").split("(")[0].split(":")[0].rstrip("!")
        if actual_type not in VALID_TYPES:
            issues.append(
                f"Unknown commit type `{actual_type}`. "
                f"Valid types: {', '.join(sorted(VALID_TYPES))}"
            )

    # --- Blank line after subject ---
    if len(lines) > 1 and lines[1].strip():
        issues.append("Missing blank line after subject line")

    # --- Body ---
    body_lines = lines[2:] if len(lines) > 2 else []

    # Strip trailing empty lines for analysis
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()

    if not body_lines:
        issues.append("Commit body is required (explain WHY the change was made)")
    else:
        # Check line length in body (allow some slack for URLs)
        for i, line in enumerate(body_lines, start=3):
            stripped = line.strip()
            if len(line) > 72 and not stripped.startswith("http") and not re.match(r"^\[.+\]:\s*http", stripped):
                issues.append(
                    f"Body line {i} is {len(line)} chars (max 72): {line!r}"
                )

    # --- Co-Authored-By ---
    co_author_re = re.compile(
        r"^Co-Authored-By: Claude [\w.]+ [\d.]+(?:\s+\([^)]+\))? <noreply@anthropic\.com>$"
    )
    has_co_author = any(co_author_re.match(line.strip()) for line in lines)
    if not has_co_author:
        # Check for common mistakes
        has_any_co_author = any("co-authored-by" in line.lower() for line in lines)
        if has_any_co_author:
            issues.append(
                "Co-Authored-By line found but doesn't match expected format: "
                "`Co-Authored-By: Claude <model-name> <noreply@anthropic.com>`"
            )
        else:
            issues.append(
                "Missing Co-Authored-By trailer. Add: "
                "`Co-Authored-By: Claude <model-name> <noreply@anthropic.com>`"
            )

    return issues


def main():
    tool_name, tool_input = parse_input()

    if tool_name != "Bash":
        approve()

    command = tool_input.get("command", "")

    commit_cmd = find_git_commit_command(command)
    if not commit_cmd:
        approve()

    # Allow --amend --no-edit (no new message needed)
    if has_flag(commit_cmd, "--no-edit"):
        approve()

    # Require -c commit.gpgsign=false (SSH signing hangs in the sandbox)
    if "commit.gpgsign=false" not in commit_cmd:
        block(
            "git commit must include `-c commit.gpgsign=false` to avoid hanging on SSH signing. "
            "Use: `git -c commit.gpgsign=false commit -F <file>`."
        )

    # --fixup and --squash auto-generate the commit message, so skip
    # -m/-F checks and message validation for them.
    if has_flag(commit_cmd, "--fixup", "--squash"):
        approve()

    # Block -m usage
    if has_flag(commit_cmd, "-m", "--message"):
        block(
            "Use `git commit -F <file>` instead of `-m`. "
            "Write the commit message to a unique temp file under `/private/tmp/claude/` "
            "(e.g., `commit-msg-<short-id>.txt`) using the Write tool first, then commit with "
            "`git -c commit.gpgsign=false commit -F /private/tmp/claude/commit-msg-<short-id>.txt`."
        )

    # Require -F
    filepath = extract_flag_value(commit_cmd, "-F") or extract_flag_value(commit_cmd, "--file")
    if not filepath:
        block(
            "git commit must use `-F <file>` to provide the commit message. "
            "Write the message to a unique temp file under `/private/tmp/claude/` first "
            "(e.g., `commit-msg-<short-id>.txt` to avoid collisions with parallel agents)."
        )

    # Validate the commit message file
    issues = validate_commit_message(filepath)
    if issues:
        block(
            "Commit message validation failed:\n"
            + "\n".join(f"  - {issue}" for issue in issues)
        )

    approve()


if __name__ == "__main__":
    main()
