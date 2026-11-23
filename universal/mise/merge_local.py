#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"  # tomllib, for TOML overlays
# ///
"""Combine a merge entry's shared source with this machine's local overlay.

A merge entry replaces the target's arrays with the source's, so entries that
belong to one machine only (a work proxy in a sandbox allowlist) can't live in
the live file. They go in an overlay instead, a file outside the repo at the
target's path under ~/.config/dotfiles/local/ (honoring XDG_CONFIG_HOME):
~/.claude/settings.json takes ~/.config/dotfiles/local/.claude/settings.json.
The overlay is in the target's format and holds only the additions.

Objects merge key by key, arrays get the overlay's items that the source lacks
appended, and any other overlay value replaces the source's. A Claude Code hook
group (an object with a `hooks` array) joins the source's group with the same
`matcher`, so its hooks are appended to that group's.

usage: merge_local.py <shared source> <overlay>
  Prints the combined source, in the format of the files' extension. The
  `.tera` templates of the merge entries call it when the overlay exists.

Imported by merge-guard.py and agents/review-settings.py, so it stays importable
on Python 3.9 (macOS's python3) as long as no TOML file is read.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def local_root() -> Path:
    config = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(config) / "dotfiles/local"


def overlay_path(target: Path) -> Path | None:
    """The overlay for a target under ~; a target elsewhere has none."""
    target = target.expanduser()
    if not target.is_relative_to(Path.home()):
        return None
    return local_root() / target.relative_to(Path.home())


class InvalidFile(ValueError):
    """A source or overlay that doesn't parse; the message names the file."""


def load(path: Path) -> object:
    text = path.read_text()
    if not text.strip():
        raise InvalidFile(f"{path}: empty file; add entries or delete it")
    try:
        if path.suffix == ".toml":
            import tomllib

            return tomllib.loads(text)
        return json.loads(text)
    except ValueError as error:  # JSONDecodeError and TOMLDecodeError
        kind = "TOML" if path.suffix == ".toml" else "JSON"
        raise InvalidFile(f"{path}: invalid {kind}: {error}") from error


def is_hook_group(item: object) -> bool:
    """A Claude Code hook group: `{"matcher": ..., "hooks": [...]}`."""
    return isinstance(item, dict) and isinstance(item.get("hooks"), list)


def matching_group(groups: list, group: dict) -> dict | None:
    """The hook group in `groups` with the same matcher as `group`."""
    matcher = group.get("matcher", "")
    return next(
        (g for g in groups if is_hook_group(g) and g.get("matcher", "") == matcher),
        None,
    )


def combine(shared: object, local: object) -> object:
    if isinstance(shared, dict) and isinstance(local, dict):
        merged = dict(shared)
        for key, value in local.items():
            merged[key] = combine(shared[key], value) if key in shared else value
        return merged
    if isinstance(shared, list) and isinstance(local, list):
        merged = list(shared)
        for item in local:
            # A hook group joins the shared group with its matcher, so a hook
            # added to a shared matcher doesn't become a second group
            group = matching_group(merged, item) if is_hook_group(item) else None
            if group is not None:
                merged[merged.index(group)] = combine(group, item)
            elif item not in merged:
                merged.append(item)
        return merged
    return local


def effective(source: Path, target: Path) -> object:
    """The keys a merge entry sets: its source, combined with the target's overlay.

    A `.tera` source is the template of the file without that suffix.
    """
    if source.suffix == ".tera":
        source = source.with_suffix("")
    data = load(source)
    overlay = overlay_path(target)
    if overlay and overlay.is_file():
        data = combine(data, load(overlay))
    return data


BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")


def toml_string(text: str) -> str:
    # JSON's escapes are all valid in a TOML basic string. JSON leaves DEL
    # unescaped, which TOML doesn't allow.
    return json.dumps(text, ensure_ascii=False).replace("\x7f", "\\u007f")


def toml_key(key: str) -> str:
    return key if BARE_KEY.fullmatch(key) else toml_string(key)


def toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return toml_string(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        pairs = (f"{toml_key(k)} = {toml_value(v)}" for k, v in value.items())
        return "{ " + ", ".join(pairs) + " }"
    return value.isoformat()  # TOML dates and times


def toml_dumps(table: dict, prefix: tuple[str, ...] = ()) -> str:
    lines = [
        f"{toml_key(k)} = {toml_value(v)}"
        for k, v in table.items()
        if not isinstance(v, dict)
    ]
    for key, value in table.items():
        if isinstance(value, dict):
            path = (*prefix, key)
            lines += ["", "[" + ".".join(map(toml_key, path)) + "]"]
            lines.append(toml_dumps(value, path))
    return "\n".join(lines).strip("\n")


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    source, overlay = map(Path, sys.argv[1:])
    try:
        data = combine(load(source), load(overlay))
    except InvalidFile as error:
        # mise prints this above its own "failed to render template"
        print(f"merge_local.py: {error}", file=sys.stderr)
        return 1
    if source.suffix == ".toml":
        print(toml_dumps(data))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
