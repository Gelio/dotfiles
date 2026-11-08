#!/usr/bin/env bash
# Parses zsh files with `zsh -n`, since ShellCheck doesn't support zsh.
set -euo pipefail

ci_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$ci_dir/.."

if ! command -v zsh >/dev/null; then
  if [[ -n "${CI:-}" ]]; then
    echo "zsh is not installed, and CI requires it" >&2
    exit 1
  fi
  echo "warning: zsh is not installed, skipping the zsh syntax check" >&2
  exit 0
fi

status=0
while IFS= read -r file; do
  zsh -n "$file" || status=1
done < <("$ci_dir/shell-files.sh" zsh)
exit "$status"
