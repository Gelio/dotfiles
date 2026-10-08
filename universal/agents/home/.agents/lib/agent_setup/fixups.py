"""Advisory fixup-scope validation shared by both agents."""
import shlex
import subprocess

def run_git(*args: str, cwd: str | None = None) -> str:
    """Run a git command and return stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git", *args], capture_output=True, text=True, timeout=5, cwd=cwd
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


def find_target_by_subject(fixup_subject: str, cwd: str | None = None) -> str | None:
    """Find the target commit SHA by matching the subject line."""
    git = lambda *args: run_git(*args, cwd=cwd)
    merge_base = git("merge-base", "HEAD", "main") or git(
        "merge-base", "HEAD", "master"
    )
    if not merge_base:
        return None

    # Search branch commits, excluding HEAD (the fixup itself)
    log_output = git("log", "--format=%H %s", f"{merge_base}..HEAD~1")
    if not log_output:
        return None

    for line in log_output.splitlines():
        sha, _, subject = line.partition(" ")
        if subject.startswith("fixup! "):
            continue  # skip other fixups
        if subject == fixup_subject:
            return sha

    return None


def check_fixup(command: str, cwd: str | None = None) -> str | None:
    if not is_commit_command(command):
        return None
    git = lambda *args: run_git(*args, cwd=cwd)
    # --- Is HEAD a fixup commit? ---
    head_subject = git("log", "-1", "--format=%s", "HEAD")
    if not head_subject or not head_subject.startswith("fixup! "):
        return None

    # --- Find the target commit ---
    target_sha = None

    # Method 1: --fixup=<ref> in the command
    target_ref = extract_fixup_target_from_command(command)
    if target_ref:
        target_sha = git("rev-parse", target_ref)

    # Method 2: match by subject
    if not target_sha:
        target_subject = head_subject.removeprefix("fixup! ")
        target_sha = find_target_by_subject(target_subject, cwd)

    if not target_sha:
        return None

    # --- Compare file sets ---
    target_files = set(
        filter(
            None,
            git(
                "diff-tree", "--no-commit-id", "-r", "--name-only", target_sha
            ).splitlines(),
        )
    )
    fixup_files = set(
        filter(
            None,
            git(
                "diff-tree", "--no-commit-id", "-r", "--name-only", "HEAD"
            ).splitlines(),
        )
    )

    if not fixup_files or not target_files:
        return None

    extra_files = sorted(fixup_files - target_files)
    if not extra_files:
        return None

    # --- Build advisory warning ---
    target_oneline = git("log", "--oneline", "-1", target_sha)

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

    return warning
