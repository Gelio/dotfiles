#!/usr/bin/env bash
# Lists the tracked shell files of one kind, one per line:
#   shell-files.sh shebang   scripts run by bash or sh (*.sh, or declared)
#   shell-files.sh bashrc    *.bashrc files, sourced and without a shebang
#   shell-files.sh zsh       zsh startup files
#
# NOTE: runs on macOS bash 3.2 too
set -euo pipefail

kind="${1:?usage: shell-files.sh shebang|bashrc|zsh}"
cd "$(git rev-parse --show-toplevel)"

excludes=(
  # Comes under the checks in the last stage of #19. Delete this line then.
  ':!ubuntu/'
  # The demo config sketchybar ships, not code maintained here.
  ':!macos/yabai/stowed/.config/sketchybar/sketchybarrc'
)

function is_zsh_file {
  case "$1" in
  *.zsh | *.zshrc | *.zshrc-dotfiles) return 0 ;;
  *) return 1 ;;
  esac
}

# A bash or sh shebang, or a ShellCheck directive in its place.
function declares_shell {
  local first_line="" shebang directive
  IFS= read -r first_line <"$1" || true
  shebang='^#![[:space:]]*(/[^[:space:]]*/)?(env[[:space:]]+)?(ba)?sh([[:space:]]|$)'
  directive='^#[[:space:]]*shellcheck[[:space:]]+shell=(ba)?sh([[:space:]]|$)'
  [[ "$first_line" =~ $shebang || "$first_line" =~ $directive ]]
}

function matches_kind {
  local file="$1"
  case "$kind" in
  shebang)
    if is_zsh_file "$file" || [[ "$file" == *.bashrc ]]; then
      return 1
    fi
    [[ "$file" == *.sh ]] || declares_shell "$file"
    ;;
  bashrc) [[ "$file" == *.bashrc ]] ;;
  zsh) is_zsh_file "$file" ;;
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
