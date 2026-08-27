#!/usr/bin/env bash
set -euo pipefail

NC='\033[0m'
Green='\033[0;32m'
Red='\033[0;31m'
Yellow='\033[0;33m'

# Resolve Windows USERPROFILE
windows_userprofile_path=$(cmd.exe /c 'echo %USERPROFILE%' 2>/dev/null | tr -d '\r')
if [[ -z "$windows_userprofile_path" ]]; then
  echo -e "${Red}Unable to find Windows USERPROFILE path${NC}"
  exit 1
fi
userprofile_path=$(wslpath "$windows_userprofile_path")

# File Mappings: "Windows_Relative_Path|Local_Path"
SYNC_MAP=(
  "AppData/Local/Microsoft/PowerToys/Keyboard Manager/default.json|./config/keyboard-manager-settings.json"
  ".glzr/glazewm/config.yaml|./config/.glzr/glazewm/config.yaml"
  ".glzr/zebar/settings.json|./config/.glzr/zebar/settings.json"
)

copy_file() {
  local src="$1"
  local dest="$2"

  if [[ ! -f "$src" ]]; then
    echo -e "${Red}Source missing: $src${NC}"
    return 1
  fi

  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  echo -e "Copied: ${Green}$src${NC} -> ${Green}$dest${NC}"
}

should_sync() {
  local entry="$1"
  local filter="${2:-}"

  # If no filter is specified, sync everything
  if [[ -z "$filter" ]]; then
    return 0
  fi

  # Case-insensitive substring match against the entire mapping entry
  shopt -s nocasematch
  if [[ "$entry" =~ $filter ]]; then
    shopt -u nocasematch
    return 0
  fi
  shopt -u nocasematch

  return 1
}

pull() {
  local filter="${1:-}"
  [[ -n "$filter" ]] && echo -e "Pulling settings matching '${Yellow}$filter${NC}'..." || echo "Pulling all settings..."

  for entry in "${SYNC_MAP[@]}"; do
    if ! should_sync "$entry" "$filter"; then
      continue
    fi

    IFS='|' read -r win_rel local_path <<<"$entry"
    win_full="$userprofile_path/$win_rel"

    if [[ "$win_rel" == *.json ]] && command -v jq &>/dev/null; then
      mkdir -p "$(dirname "$local_path")"
      jq . <"$win_full" >"$local_path"
      echo -e "Formatted & Copied: ${Green}$win_full${NC} -> ${Green}$local_path${NC}"
    else
      copy_file "$win_full" "$local_path"
    fi
  done
}

push() {
  local filter="${1:-}"
  [[ -n "$filter" ]] && echo -e "Pushing settings matching '${Yellow}$filter${NC}'..." || echo "Pushing all settings..."

  for entry in "${SYNC_MAP[@]}"; do
    if ! should_sync "$entry" "$filter"; then
      continue
    fi

    IFS='|' read -r win_rel local_path <<<"$entry"
    win_full="$userprofile_path/$win_rel"
    copy_file "$local_path" "$win_full"
  done
}

# Subcommand Router
case "${1:-}" in
pull)
  pull "${2:-}"
  ;;
push)
  push "${2:-}"
  ;;
*)
  echo "Usage: $0 {push|pull} [filter]"
  echo "Examples:"
  echo "  $0 push glzr"
  echo "  $0 pull keyboard"
  exit 1
  ;;
esac
