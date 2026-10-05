#!/usr/bin/env python3
"""Install shared resources and merge only the selected agents' settings."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import tomllib
from typing import Any

ROOT = Path(__file__).resolve().parent
SETTINGS = {
    'claude': ('.claude/settings.json', 'settings-partial.json'),
    'codex': ('.codex/hooks.json', 'codex-hooks-partial.json'),
}
CODEX_CONFIG = ('.codex/config.toml', 'codex-config-partial.toml')


def same_hook(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (a.get('type'), a.get('command'), a.get('if')) == (b.get('type'), b.get('command'), b.get('if'))


def deep_merge(target: object, source: object) -> object:
    """Objects merge recursively, arrays union by value, scalars from `source` win."""
    if isinstance(target, list) and isinstance(source, list):
        return target + [item for item in source if item not in target]
    if isinstance(target, dict) and isinstance(source, dict):
        result = dict(target)
        for key, value in source.items():
            result[key] = deep_merge(result[key], value) if key in result else value
        return result
    return source


def merge_hooks(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    """Append missing hook commands per matcher; never remove existing ones."""
    result = dict(target)
    for event, source_matchers in source.items():
        merged = [{**m, 'hooks': list(m.get('hooks', []))} for m in result.get(event, [])]
        for source_matcher in source_matchers:
            existing = next((m for m in merged if m.get('matcher') == source_matcher.get('matcher')), None)
            if existing is None:
                merged.append(source_matcher)
                continue
            for hook in source_matcher['hooks']:
                if not any(same_hook(h, hook) for h in existing['hooks']):
                    existing['hooks'].append(hook)
        result[event] = merged
    return result


def merge_settings(home: Path, agent: str) -> None:
    """Additively merge the agent's partial into its settings; back up changes."""
    relative, partial_name = SETTINGS[agent]
    path = home / relative
    settings: dict[str, Any] = json.loads(path.read_text()) if path.exists() else {}
    partial: dict[str, Any] = json.loads((ROOT / partial_name).read_text())
    if 'hooks' in partial:
        settings['hooks'] = merge_hooks(settings.get('hooks', {}), partial.pop('hooks'))
    serialized = json.dumps(deep_merge(settings, partial), indent=2, ensure_ascii=False) + '\n'
    if path.exists() and path.read_text() == serialized:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, f'{path}.backup-{int(time.time() * 1000)}')
    temporary = path.with_name(f'{path.name}.tmp-{os.getpid()}')
    # Create private from the start; settings can hold credentials in `env`.
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as stream:
        stream.write(serialized)
    temporary.replace(path)
    print(f'Merged {partial_name} into {path}')


def toml_value(value: object) -> str:
    """Serialize the scalar and flat-array values the Codex partial uses."""
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, list):
        return '[' + ', '.join(toml_value(item) for item in value) + ']'
    # JSON string escapes are valid TOML basic-string escapes.
    return json.dumps(value, ensure_ascii=False)


def merge_codex_config(home: Path) -> None:
    """Add the partial's missing `[table]` keys to Codex's config.toml as text.

    Codex rewrites this file itself (project trust, hook state), so it can't be
    stowed, and there is no stdlib TOML writer. Inserting lines keeps Codex's
    formatting and comments intact. Keys already present are left alone, even
    with a different value; change those by hand.
    """
    relative, partial_name = CODEX_CONFIG
    path = home / relative
    original = path.read_text() if path.exists() else ''
    config = tomllib.loads(original)
    lines = original.splitlines(keepends=True)
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'
    for table, values in tomllib.loads((ROOT / partial_name).read_text()).items():
        existing = config.get(table, {})
        missing = [f'{key} = {toml_value(value)}\n' for key, value in values.items() if key not in existing]
        for key, value in values.items():
            if key in existing and existing[key] != value:
                print(f'Keeping {table}.{key} in {path}; it differs from {partial_name}')
        if not missing:
            continue
        header = next((i for i, line in enumerate(lines) if line.split('#')[0].strip() == f'[{table}]'), None)
        if header is None:
            lines += (['\n'] if lines else []) + [f'[{table}]\n', *missing]
        else:
            lines[header + 1:header + 1] = missing
    merged = ''.join(lines)
    if merged == original:
        return
    tomllib.loads(merged)  # never write a config Codex can't load
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, f'{path}.backup-{int(time.time() * 1000)}')
    temporary = path.with_name(f'{path.name}.tmp-{os.getpid()}')
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as stream:
        stream.write(merged)
    temporary.replace(path)
    print(f'Merged {partial_name} into {path}')


class Args(argparse.Namespace):
    """Typed `parse_args` result; argparse keeps these defaults when a flag is absent."""
    agent: str = 'claude'
    target_home: Path = Path.home()
    dry_run: bool = False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=['claude', 'codex', 'both'])
    parser.add_argument('--target-home', type=Path, help='isolated installation target (default: current home)')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(namespace=Args())
    home = args.target_home.expanduser().resolve()
    # Shared resources belong to Stow. Settings, handoffs, and third-party skills do not.
    if not args.dry_run:
        for directory in ['.agents/skills', '.agents/lib', '.claude/skills', '.claude/hooks', '.codex/hooks', '.local/bin', '.local/agent-handoffs']:
            (home / directory).mkdir(parents=True, exist_ok=True)
    if not home.is_dir():
        parser.error('target home must exist for a dry run')
    stow = ['stow', '-R', '-d', str(ROOT), '-t', str(home), 'stowed']
    # Detect unmanaged conflicts before changing any links or settings.
    subprocess.run([*stow, '--simulate'], check=True)
    agents = ['claude', 'codex'] if args.agent == 'both' else [args.agent]
    for agent in agents:
        settings = home / SETTINGS[agent][0]
        if settings.exists() and not isinstance(json.loads(settings.read_text()), dict):
            parser.error(f'Settings must contain a JSON object: {settings}')
    codex_config = home / CODEX_CONFIG[0]
    if 'codex' in agents and codex_config.exists():
        try:
            tomllib.loads(codex_config.read_text())
        except tomllib.TOMLDecodeError as error:
            parser.error(f'Invalid TOML in {codex_config}: {error}')
    if not args.dry_run:
        subprocess.run(stow, check=True)
        for agent in agents:
            merge_settings(home, agent)
        if 'codex' in agents:
            merge_codex_config(home)
    print(f'{"Would install" if args.dry_run else "Installed"}: shared resources + {", ".join(agents)} settings in {home}')
    if 'codex' in agents:
        print('Restart Codex and review/trust the hook definitions when prompted.')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
