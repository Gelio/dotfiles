#!/usr/bin/env python3
"""Copy third-party skills from GitHub into home/.agents/skills.

vendored-skills.json lists each skill's upstream repo, folder and pinned
commit. By default this re-copies every skill at its pinned commit; --latest
moves the pins to each repo's default branch first. Review the result with
git diff: upstream changes and any local edits it overwrote both show there.
A skill folder without its own license gets the repo's LICENSE file.
"""

import argparse
import io
import json
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "vendored-skills.json"
SKILLS = ROOT / "home/.agents/skills"
CLAUDE_SKILLS = ROOT / "home/.claude/skills"
OXFMTRC = ROOT.parent.parent / ".oxfmtrc.jsonc"


def latest_commit(repo: str) -> str:
    out = subprocess.run(
        ["git", "ls-remote", f"https://github.com/{repo}.git", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return out.split()[0]


def fetch_tarball(repo: str, commit: str) -> tarfile.TarFile:
    url = f"https://codeload.github.com/{repo}/tar.gz/{commit}"
    with urllib.request.urlopen(url, timeout=60) as response:
        data: bytes = response.read()
    return tarfile.open(fileobj=io.BytesIO(data), mode="r:gz")


LICENSE_NAMES = {"LICENSE", "LICENSE.md", "LICENSE.txt"}


def extract_folder(archive: tarfile.TarFile, folder: PurePosixPath, dest: Path):
    """Extract one folder of a GitHub tarball (prefixed <repo>-<sha>/) to dest."""
    found = False
    root_license = None
    for member in archive.getmembers():
        parts = PurePosixPath(member.name).parts
        relative = PurePosixPath(*parts[1:]) if len(parts) > 1 else None
        if len(parts) == 2 and parts[1] in LICENSE_NAMES and member.isfile():
            root_license = member
        if relative is None or not relative.is_relative_to(folder):
            continue
        if not (member.isfile() or member.isdir()):
            sys.exit(f"Refusing {member.name}: not a regular file or folder")
        found = True
        target = dest / relative.relative_to(folder)
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        _ = target.write_bytes(read_member(archive, member))
        target.chmod(0o755 if member.mode & 0o111 else 0o644)
    if not found:
        sys.exit(f"{folder} not found in the archive")
    has_license = any((dest / name).exists() for name in LICENSE_NAMES)
    if root_license and not has_license:
        license_path = dest / PurePosixPath(root_license.name).name
        _ = license_path.write_bytes(read_member(archive, root_license))


def read_member(archive: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    file = archive.extractfile(member)
    assert file is not None
    return file.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*", help="skills to update (default: all)")
    parser.add_argument(
        "--latest",
        action="store_true",
        help="move the pins to each repo's default branch",
    )
    args = parser.parse_args()

    manifest: dict[str, dict[str, str]] = json.loads(MANIFEST.read_text())
    unknown = set(args.names) - manifest.keys()
    if unknown:
        parser.error(f"not in {MANIFEST.name}: {', '.join(sorted(unknown))}")
    names = args.names or sorted(manifest)

    commits: dict[str, str] = {}
    archives: dict[tuple[str, str], tarfile.TarFile] = {}
    for name in names:
        skill = manifest[name]
        repo = skill["repo"]
        if args.latest:
            if repo not in commits:
                commits[repo] = latest_commit(repo)
            skill["commit"] = commits[repo]
        key = (repo, skill["commit"])
        if key not in archives:
            archives[key] = fetch_tarball(*key)

        dest = SKILLS / name
        shutil.rmtree(dest, ignore_errors=True)
        extract_folder(archives[key], PurePosixPath(skill["path"]), dest)

        link = CLAUDE_SKILLS / name
        if not link.is_symlink():
            link.symlink_to(Path("../../.agents/skills") / name)
        print(f"{name}: {repo}@{skill['commit'][:12]}", flush=True)

    _ = MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    # Upstream's files keep upstream's formatting
    ignored = OXFMTRC.read_text()
    missing = [
        name
        for name in manifest
        if f'"universal/agents/home/.agents/skills/{name}/"' not in ignored
    ]
    if missing:
        print(f"\nAdd these to the vendored ignorePatterns in {OXFMTRC.name}:")
        for name in missing:
            print(f'    "universal/agents/home/.agents/skills/{name}/",')

    print("\nReview with: git diff --stat -- home/.agents/skills")


if __name__ == "__main__":
    main()
