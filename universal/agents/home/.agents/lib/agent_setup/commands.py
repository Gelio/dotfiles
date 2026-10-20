"""Command policy, independent of hook transport and agent sandbox flags."""
import os
import re
import shlex
import subprocess
from collections.abc import Iterable

def get_parts(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def _program_index(parts: list[str], name: str) -> int:
    """Index of `name` as a program (`/usr/bin/git` counts), or -1."""
    return next((i for i, p in enumerate(parts) if os.path.basename(p) == name), -1)


def find_git_subcommand(parts: list[str]) -> tuple[int, str | None]:
    """Find the git subcommand, skipping git-level flags like -c key=value."""
    i = _program_index(parts, "git")
    if i < 0:
        return -1, None
    i += 1  # skip 'git'
    while i < len(parts):
        if parts[i] in ("-c", "--config", "-C", "--config-env"):
            i += 2
        elif parts[i].startswith("-"):
            i += 1
        else:
            break
    if i >= len(parts):
        return -1, None
    return i, parts[i]


def _git(args: list[str], cwd: str | None) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=cwd or None,
                                capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _git_dir(parts: list[str], sub_idx: int, cwd: str | None) -> str | None:
    """Apply `git -C <dir>` options to the hook's cwd."""
    directory = cwd
    for i in range(sub_idx):
        if parts[i] == "-C" and i + 1 < sub_idx:
            directory = os.path.join(directory or os.getcwd(), parts[i + 1])
    return directory


# Config that changes where or what an otherwise-checked push sends.
PUSH_CONFIG_KEY = re.compile(
    r"^(remote\..+\.(push|mirror|url|pushurl)|push\..+|url\..+\.(pushinsteadof|insteadof))$",
    re.IGNORECASE)


def _config_overrides(parts: list[str], sub_idx: int) -> list[str]:
    """Config keys set by `-c`, `--config-env` or GIT_CONFIG* env before the subcommand."""
    keys: list[str] = []
    for i, p in enumerate(parts[:sub_idx]):
        if p in ("-c", "--config-env") and i + 1 < sub_idx:
            keys.append(parts[i + 1].split("=", 1)[0])
        elif p.startswith("--config-env="):
            keys.append(p.split("=", 2)[1])
        elif p.startswith("GIT_CONFIG"):
            keys.append(p.split("=", 1)[0])
    return keys


PUSH_BLOCKED_FLAGS = {
    "--force": "force pushes", "--force-with-lease": "force pushes",
    "--force-if-includes": "force pushes", "--delete": "branch deletions",
    "--mirror": "mirror pushes", "--all": "pushes of every branch",
    "--branches": "pushes of every branch", "--prune": "pushes with --prune",
    "--tags": "tag pushes", "--follow-tags": "tag pushes",
}
PUSH_BLOCKED_SHORT = {"f": "force pushes", "d": "branch deletions"}
PUSH_VALUE_FLAGS = {"-o", "--push-option", "--receive-pack", "--exec"}
PROTECTED_BRANCHES = {"main", "master", "develop", "trunk"}


def _push_blocked(what: str) -> str:
    return (f"git push: {what} are blocked. Agents may push feature branches "
            "only; do this one manually.")


def _long_flag(arg: str, flags: Iterable[str]) -> str | None:
    """Match a long option the way git does: any unambiguous prefix counts."""
    name = arg.split("=", 1)[0]
    if len(name) < 3:
        return None
    return next((f for f in flags if f.startswith(name)), None)


def _protected_branches(git_dir: str | None) -> set[str]:
    protected = set(PROTECTED_BRANCHES)
    heads = _git(["for-each-ref", "--format=%(symref:lstrip=3)", "refs/remotes/*/HEAD"], git_dir)
    protected.update(h for h in (heads or "").splitlines() if h)
    return protected


def _push_destination(dst: str, git_dir: str | None) -> tuple[str, str]:
    """Classify a refspec destination as ("tag" | "branch", name), resolving
    git's DWIM forms: `refs/heads/x`, `heads/x`, `refs/tags/x`, `tags/x`."""
    rest = dst.removeprefix("refs/")
    if rest.startswith("tags/"):
        return "tag", rest.removeprefix("tags/")
    if rest.startswith("heads/"):
        return "branch", rest.removeprefix("heads/")
    if (not dst.startswith("refs/")
            and _git(["rev-parse", "--verify", "--quiet", f"refs/tags/{dst}"], git_dir)
            and not _git(["rev-parse", "--verify", "--quiet", f"refs/heads/{dst}"], git_dir)):
        return "tag", dst
    return "branch", dst


def check_git_push(parts: list[str], sub_idx: int, cwd: str | None) -> str | None:
    """Allow plain pushes of feature branches to a configured remote; block
    protected branches, history rewrites, deletions and tags."""
    if any(PUSH_CONFIG_KEY.match(k) or k.startswith("GIT_CONFIG")
           for k in _config_overrides(parts, sub_idx)):
        return _push_blocked("pushes with push-related config overrides")
    positional: list[str] = []
    repo: str | None = None
    i = sub_idx + 1
    while i < len(parts):
        p = parts[i]
        if p == "--":
            positional += parts[i + 1:]
            break
        if p in PUSH_VALUE_FLAGS:
            i += 2
            continue
        if p.startswith("--"):
            if _long_flag(p, ["--repo"]):
                if "=" in p:
                    repo = p.split("=", 1)[1]
                else:
                    repo = parts[i + 1] if i + 1 < len(parts) else ""
                    i += 1
                i += 1
                continue
            blocked = _long_flag(p, PUSH_BLOCKED_FLAGS)
            if blocked:
                return _push_blocked(PUSH_BLOCKED_FLAGS[blocked])
        elif p.startswith("-") and len(p) > 1:
            for ch in p[1:]:
                if ch == "o":  # the rest of the bundle is -o's value
                    break
                if ch in PUSH_BLOCKED_SHORT:
                    return _push_blocked(PUSH_BLOCKED_SHORT[ch])
        else:
            positional.append(p)
        i += 1

    git_dir = _git_dir(parts, sub_idx, cwd)
    # With --repo, every positional argument is a refspec.
    remote = repo if repo is not None else (positional[0] if positional else None)
    refspecs = positional if repo is not None else positional[1:]
    if remote is not None and remote not in (_git(["remote"], git_dir) or "").split():
        return _push_blocked(f"pushes to `{remote}`, which is not a configured remote,")
    if "true" in (_git(["config", "--get-regexp", r"^remote\..*\.mirror$"], git_dir) or "").lower():
        return _push_blocked("pushes while a remote is configured as a mirror")
    # remote.*.push remaps branch names and push.default decides what a bare
    # push sends; fail closed unless each refspec names its destination.
    if (any(":" not in s for s in refspecs) or not refspecs) and _git(
            ["config", "--get-regexp", r"^remote\..*\.push$"], git_dir):
        return _push_blocked("pushes without an explicit `src:dst` while remote.*.push is configured")
    if not refspecs:
        if (_git(["config", "push.default"], git_dir) or "simple") not in ("simple", "current"):
            return _push_blocked("implicit pushes with a non-simple push.default")
        refspecs = ["HEAD"]
    protected = _protected_branches(git_dir)

    for spec in refspecs:
        if spec.startswith("+"):
            return _push_blocked("force pushes")
        if spec.startswith(":"):
            return _push_blocked("branch deletions")
        if "*" in spec:
            return _push_blocked("wildcard refspecs")
        dst = spec.rsplit(":", 1)[-1]
        if dst in ("HEAD", "@"):
            dst = _git(["symbolic-ref", "--quiet", "--short", "HEAD"], git_dir)
            if not dst:
                return _push_blocked("pushes from a detached or unknown HEAD")
        kind, name = _push_destination(dst, git_dir)
        if kind == "tag":
            return _push_blocked("tag pushes")
        if name in protected or name.startswith("release/"):
            return _push_blocked(f"pushes to protected branches ({name})")
    return None


CONFIG_READ_FLAGS = {"--get", "--get-all", "--get-regexp", "--list", "-l", "get", "list"}


def check_push_config(args: list[str]) -> str | None:
    """Push config decides what a `git push` sends; keep it user-owned."""
    if CONFIG_READ_FLAGS & set(args):
        return None
    if any(PUSH_CONFIG_KEY.match(a) for a in args):
        return "Changing push configuration (push.*, remote.*.push/mirror/url) is blocked — do it manually."
    if any(a.lower().startswith("alias.") for a in args) and any("push" in a for a in args):
        return "Defining git aliases that push is blocked — do it manually."
    return None


def check_risky_git(command: str, cwd: str | None = None) -> str | None:
    parts = get_parts(command)
    sub_idx, sub = find_git_subcommand(parts)
    if sub == "push":
        return check_git_push(parts, sub_idx, cwd)
    if sub == "config":
        return check_push_config(parts[sub_idx + 1:])
    if sub == "remote" and any(p.startswith("--mirror") for p in parts[sub_idx + 1:]):
        return "git remote --mirror is blocked — configure mirrors manually."
    return None


RISKY_GH_COMMANDS: dict[tuple[str, ...], str] = {
    ("pr", "merge"): "gh pr merge is blocked — merge PRs manually after review.",
    ("pr", "close"): "gh pr close is blocked — close PRs manually.",
    ("issue", "close"): "gh issue close is blocked — close issues manually.",
    ("release", "create"): "gh release create is blocked — create releases manually.",
    ("release", "delete"): "gh release delete is blocked — delete releases manually.",
    ("repo", "delete"): "gh repo delete is blocked — delete repositories manually.",
}


def check_risky_gh(command: str) -> str | None:
    parts = get_parts(command)
    i = 0
    while i < len(parts) and (parts[i] == "env" or re.match(r"^\w+=", parts[i])):
        i += 1
    if i >= len(parts) or os.path.basename(parts[i]) != "gh":
        return None
    args = parts[i + 1:]
    if args[:1] == ["api"]:
        method = next((a.split("=", 1)[1] if "=" in a else args[j + 1]
                       for j, a in enumerate(args)
                       if (a in ("-X", "--method") and j + 1 < len(args))
                       or a.startswith("--method=")), "GET").upper()
        if method == "DELETE" or (method == "PUT" and any(a.endswith("/merge") for a in args)):
            return f"gh api {method} is blocked here — delete or merge through GitHub manually."
        return None
    # Match the command group and action, not any token: `--body close` is fine.
    words: list[str] = []
    j = 0
    while j < len(args) and len(words) < 2:
        if args[j] in ("-R", "--repo"):
            j += 2
            continue
        if not args[j].startswith("-"):
            words.append(args[j])
        j += 1
    return RISKY_GH_COMMANDS.get(tuple(words))


RM_DANGEROUS_TARGETS = {"/", "/*", "~", "~/", "~/*", ".", "./", "./*", "*", ".git", "{}"}
# Paths under .git whose removal loses history; `.git/rebase-merge` etc. stay allowed.
GIT_HISTORY = {"objects", "refs", "logs", "packed-refs", "HEAD"}


def _strictly_inside(path: str, roots: list[str]) -> bool:
    return any(path != root and path.startswith(root.rstrip("/") + "/") for root in roots)


def _rm_target_reason(target: str, cwd: str, root: str) -> str | None:
    """`cwd` is where the segment runs (after any `cd`); `root` is the
    session's working directory, the only non-temp tree rm -rf may touch."""
    if (target in RM_DANGEROUS_TARGETS or target.startswith("~")
            or ".." in target.split("/")):
        return f"rm -rf {target} is blocked."
    if any(c in target for c in "`{}") or (
            "$" in target and not re.match(r"\$\{?TMPDIR\}?/[^$`]+$", target)):
        return f"rm -rf {target} is blocked — expansions may produce an unexpected path."
    path = os.path.normpath(os.path.join(cwd, target))
    # For a glob, the directory it expands in must itself be inside a root.
    components = path.split("/")
    glob_at = next((i for i, c in enumerate(components) if any(g in c for g in "*?[")), None)
    if glob_at is not None:
        resolved = os.path.realpath("/".join(components[:glob_at]) or "/")
    elif target.endswith("/"):
        resolved = os.path.realpath(path)  # a trailing slash follows a symlink
    else:
        resolved = os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path))
    parts = resolved.split("/")
    if parts[-1] == ".git" or any(
            p == ".git" and nxt in GIT_HISTORY for p, nxt in zip(parts, parts[1:])):
        return f"rm -rf {target} is blocked — it would delete git history."
    roots = [os.path.realpath(r) for r in (root, "/tmp", os.environ.get("TMPDIR") or "/tmp")]
    # The working directory itself is off limits even when it sits under /tmp.
    if resolved == roots[0] or not _strictly_inside(resolved, roots):
        return f"rm -rf {target} is blocked — it is outside the working directory and temp dirs."
    return None


def check_rm_rf(command: str, sandboxed: bool = False, cwd: str | None = None,
                root: str | None = None) -> str | None:
    """Sandboxed: allow recursive rm of paths inside the working directory or
    temp dirs. Unsandboxed: block recursive rm entirely."""
    parts = get_parts(command)
    rm = _program_index(parts, "rm")
    # `git rm` only removes tracked files, which git can restore.
    if rm < 0 or find_git_subcommand(parts)[1] == "rm":
        return None
    args = parts[rm + 1:]
    recursive = False
    targets: list[str] = []
    for i, arg in enumerate(args):
        if arg == "--":
            targets += args[i + 1:]
            break
        if arg.startswith("--"):
            recursive |= _long_flag(arg, ["--recursive"]) is not None
        elif arg.startswith("-") and len(arg) > 1:
            recursive |= "r" in arg or "R" in arg
        else:
            targets.append(arg)
    # rm -r deletes without prompting in a non-interactive shell, so -f adds nothing.
    if not recursive:
        return None
    if not sandboxed:
        return "rm -rf is blocked outside the sandbox — too risky for automated execution."
    if not targets:
        return "rm -rf without explicit targets (e.g. via xargs) is blocked."
    cwd = cwd or os.getcwd()
    for target in targets:
        reason = _rm_target_reason(target, cwd, root or cwd)
        if reason:
            return reason
    return None


def _cd_target(parts: list[str], cwd: str) -> str | None:
    """Follow `cd`/`pushd` so later segments are checked where they run;
    None when the destination can't be known statically."""
    if len(parts) > 2:
        return None
    arg = parts[1] if len(parts) > 1 else "~"
    if any(c in arg for c in "$`") or arg.startswith("-"):
        return None
    return os.path.normpath(os.path.join(cwd, os.path.expanduser(arg)))


# Command separators: && || ; newline | |& and a lone & (not >& or &>).
SEPARATORS = re.compile(r"\s*(?:&&|\|\||;|\n|\|&?|(?<![<>&])&(?![>&]))\s*")


def check_command(command: str, cwd: str | None = None, sandboxed: bool = False) -> str | None:
    # Advisory enforcement, not a complete shell parser or sandbox boundary.
    root = cwd or os.getcwd()
    current: str | None = root
    for segment in SEPARATORS.split(command.replace("\\\n", " ")):
        segment = segment.strip().lstrip("(").rstrip(")").strip()
        if not segment:
            continue
        parts = get_parts(segment)
        if parts and parts[0] in ("cd", "pushd"):
            current = _cd_target(parts, current) if current else None
            continue
        if current is None:
            if find_git_subcommand(parts)[1] == "push" or _program_index(parts, "rm") >= 0:
                return ("git push and rm -rf after a `cd` the hook can't follow are blocked; "
                        "cd to a literal path or pass the path directly.")
            continue
        reason = (check_risky_git(segment, current) or check_risky_gh(segment)
                  or check_rm_rf(segment, sandboxed, current, root))
        if reason:
            return reason
    return None
