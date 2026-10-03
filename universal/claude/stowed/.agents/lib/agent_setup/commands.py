"""Command policy, independent of hook transport and agent sandbox flags."""
import re
import shlex

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


def check_command(command: str) -> str | None:
    # Preserve the existing Claude policy; this is advisory enforcement,
    # not a complete shell parser or sandbox boundary.
    for segment in re.split(r'\s*(?:&&|\|\||;)\s*', command):
        if not segment.strip():
            continue
        for check in (check_risky_git, check_risky_gh, check_rm_rf):
            reason = check(segment.strip())
            if reason:
                return reason
    return None
