#!/usr/bin/env bash
# Lists the tracked source files of one language, one per line:
#   source-files.sh lua      *.lua files
#   source-files.sh python   *.py files and scripts with a python shebang
#   source-files.sh format   Markdown, JSON and YAML files
#
# NOTE: runs on macOS bash 3.2 too
set -euo pipefail

kind="${1:?usage: source-files.sh lua|python|format}"
cd "$(git rev-parse --show-toplevel)"

excludes=(
  # Comes under the checks in the last stage of #19. Delete this line then.
  ':!ubuntu/'
)

function declares_python {
  local first_line=""
  IFS= read -r first_line <"$1" || true
  [[ "$first_line" =~ ^#![[:space:]]*(/[^[:space:]]*/)?(env[[:space:]]+)?python[0-9.]*([[:space:]]|$) ]]
}

function matches_kind {
  local file="$1"
  case "$kind" in
  lua) [[ "$file" == *.lua ]] ;;
  python) [[ "$file" == *.py ]] || declares_python "$file" ;;
  format) [[ "$file" =~ \.(md|json|jsonc|ya?ml)$ ]] ;;
  *)
    echo "Unknown kind: $kind" >&2
    exit 2
    ;;
  esac
}

git ls-files -z -- . "${excludes[@]}" |
  while IFS= read -r -d '' file; do
    # Symlinks point at files listed under their own path
    if [[ -f "$file" && ! -L "$file" ]] && matches_kind "$file"; then
      printf '%s\n' "$file"
    fi
  done
