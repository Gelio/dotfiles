#!/usr/bin/env python3
"""PreToolUse hook: enforce the Claude-specific parts of git commit hygiene.

Message *formatting* (subject length/format/type, blank line, body wrap) is
enforced natively by the global git commit-msg hook `commit-msg-lint`
(git config-based hook, see ~/.config/git.gitconfig) for every commit, so it
is intentionally NOT duplicated here. This hook only covers what git cannot:

1. git commit must use -F (not -m) — keeps Claude writing messages to a file.
2. The message file must carry the Co-Authored-By: Claude trailer.

Note: this hook does not fire on commits run with dangerouslyDisableSandbox
(e.g. SSH-signed commits), so treat it as best-effort shaping of Claude's
normal path — the git commit-msg hook is the reliable gate for message format.
"""

import json
import os
import re
import shlex
import sys


def parse_input():
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    # cwd of the tool call; -F paths may be relative to it, not the hook's cwd.
    cwd = data.get("cwd", "")
    return tool_name, tool_input, cwd


def resolve_path(filepath: str, cwd: str) -> str:
    """Resolve a shell path the way the shell would: expand ~ and env vars,
    then anchor relative paths to the command's cwd (not the hook's)."""
    p = os.path.expanduser(os.path.expandvars(filepath))
    if not os.path.isabs(p) and cwd:
        p = os.path.join(cwd, p)
    return p


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
    prefixes = tuple(f"{flag}=" for flag in flags)
    return any(p in flags or p.startswith(prefixes) for p in parts)


CO_AUTHOR_RE = re.compile(
    r"^Co-Authored-By: Claude [\w.]+ [\d.]+(?:\s+\([^)]+\))? <noreply@anthropic\.com>$"
)


def validate_co_author(filepath: str) -> list[str]:
    """Return issues if the Co-Authored-By: Claude trailer is missing/malformed.

    Message formatting is enforced by the git commit-msg hook, not here.
    """
    try:
        with open(filepath) as f:
            lines = f.read().split("\n")
    except FileNotFoundError:
        return [f"Commit message file not found: {filepath}"]
    except OSError as e:
        return [f"Cannot read commit message file: {e}"]

    if any(CO_AUTHOR_RE.match(line.strip()) for line in lines):
        return []
    if any("co-authored-by" in line.lower() for line in lines):
        return [
            "Co-Authored-By line found but doesn't match expected format: "
            "`Co-Authored-By: Claude <model-name> <version> <noreply@anthropic.com>`"
        ]
    return [
        "Missing Co-Authored-By trailer. Add: "
        "`Co-Authored-By: Claude <model-name> <version> <noreply@anthropic.com>`"
    ]


def main():
    tool_name, tool_input, cwd = parse_input()

    if tool_name != "Bash":
        approve()

    command = tool_input.get("command", "")

    commit_cmd = find_git_commit_command(command)
    if not commit_cmd:
        approve()

    # Allow --amend --no-edit (no new message needed)
    if has_flag(commit_cmd, "--no-edit"):
        approve()

    # --fixup and --squash auto-generate the commit message, so skip
    # -m/-F checks and message validation for them.
    if has_flag(commit_cmd, "--fixup", "--squash"):
        approve()

    # Block -m usage
    if has_flag(commit_cmd, "-m", "--message"):
        block(
            "Use `git commit -F <file>` instead of `-m`. "
            "Write the commit message to a unique temp file under `/tmp/claude/` "
            "(e.g., `commit-msg-<short-id>.txt`) using the Write tool first, then commit with "
            "`git commit -F /tmp/claude/commit-msg-<short-id>.txt`."
        )

    # Require -F
    filepath = extract_flag_value(commit_cmd, "-F") or extract_flag_value(commit_cmd, "--file")
    if not filepath:
        block(
            "git commit must use `-F <file>` to provide the commit message. "
            "Write the message to a unique temp file under `/tmp/claude/` first "
            "(e.g., `commit-msg-<short-id>.txt` to avoid collisions with parallel agents)."
        )

    # Only the Co-Author trailer is checked here; git enforces message format.
    issues = validate_co_author(resolve_path(filepath, cwd))
    if issues:
        block(
            "Commit message validation failed:\n"
            + "\n".join(f"  - {issue}" for issue in issues)
        )

    approve()


if __name__ == "__main__":
    main()
