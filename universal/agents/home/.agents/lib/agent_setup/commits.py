"""Commit-file policy; Git commit-msg hooks enforce message formatting."""
import shlex

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

    Handles shell operators (&&, ||, ;, |) AND newline separators, so a commit
    written as a heredoc followed by `git commit -F msg && git log` (its own
    line) is still found. shlex collapses newlines into whitespace, hiding
    segment boundaries, so split on physical lines first (after joining `\\`
    line-continuations). A heredoc body line literally starting with
    `git commit` could false-positive, causing only a spurious validation.
    Returns the sub-command string if found, None otherwise.
    """
    normalized = command.replace("\\\n", " ")
    for line in normalized.split("\n"):
        try:
            parts = shlex.split(line)
        except ValueError:
            parts = line.split()

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


def has_flag(command: str, *flags: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    prefixes = tuple(f"{flag}=" for flag in flags)
    return any(p in flags or p.startswith(prefixes) for p in parts)


def check_commit(command: str) -> str | None:
    commit_cmd = find_git_commit_command(command)
    if not commit_cmd:
        return None

    # Allow --amend --no-edit (no new message needed)
    if has_flag(commit_cmd, "--no-edit"):
        return None

    # --fixup and --squash auto-generate the commit message, so skip
    # the -m/-F checks for them.
    if has_flag(commit_cmd, "--fixup", "--squash"):
        return None

    # Block -m usage
    if has_flag(commit_cmd, "-m", "--message"):
        return (
            "Use `git commit -F <file>` instead of `-m`. "
            "Write the commit message to a unique temp file under `/tmp/agent-work/` "
            "(e.g., `commit-msg-<short-id>.txt`) using the agent's file-edit tool first, then commit with "
            "`git commit -F /tmp/agent-work/commit-msg-<short-id>.txt`."
        )

    # Require -F so multi-line messages never pass through shell quoting.
    if not has_flag(commit_cmd, "-F", "--file"):
        return (
            "git commit must use `-F <file>` to provide the commit message. "
            "Write the message to a unique temp file under `/tmp/agent-work/` first "
            "(e.g., `commit-msg-<short-id>.txt` to avoid collisions with parallel agents)."
        )

    return None
