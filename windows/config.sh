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
  ".glzr/zebar/sakyasumedh.aurora@1.0.0-modified/|./config/.glzr/zebar/sakyasumedh.aurora@1.0.0-modified/"
  "AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json|./config/windows-terminal-settings.json"
)

copy_entry() {
  local force="$1"
  local src="$2"
  local dest="$3"

  if [[ ! -e "$src" ]]; then
    echo -e "${Red}Source missing: $src${NC}"
    return 1
  fi

  if [[ -d "$src" ]]; then
    mkdir -p "$dest"

    # Check if files would be deleted and bail if force flag is missing
    if [[ "$force" != "-f" ]]; then
      local deletions
      deletions=$(rsync -a --delete --dry-run -v "$src/" "$dest/" 2>/dev/null | grep '^deleting ' || true)

      if [[ -n "$deletions" ]]; then
        echo -e "${Red}Error${NC}: Sync would delete destination files in ${Yellow}$dest${NC}. Use ${Yellow}-f${NC} or ${Yellow}--force${NC} to proceed."
        echo "${deletions//deleting/-}"
        return 1
      fi
    fi

    rsync -a --delete "$src/" "$dest/"
    echo -e "Synced directory: ${Green}$src${NC} ->${Green}$dest${NC}"
  elif [[ -f "$src" ]]; then
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
    echo -e "Copied: ${Green}$src${NC} -> ${Green}$dest${NC}"
  fi

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
  local force="$1"
  local filter="$2"
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
      copy_entry "$force" "$win_full" "$local_path"
    fi
  done
}

push() {
  local force="$1"
  local filter="$2"
  [[ -n "$filter" ]] && echo -e "Pushing settings matching '${Yellow}$filter${NC}'..." || echo "Pushing all settings..."

  for entry in "${SYNC_MAP[@]}"; do
    if ! should_sync "$entry" "$filter"; then
      continue
    fi

    IFS='|' read -r win_rel local_path <<<"$entry"
    win_full="$userprofile_path/$win_rel"
    copy_entry "$force" "$local_path" "$win_full"
  done
}

list() {
  echo "Entries to sync:"

  for entry in "${SYNC_MAP[@]}"; do
    IFS='|' read -r win_rel local_path <<<"$entry"
    local suffix=""
    if [[ -d "$local_path" ]]; then
      suffix=" ${Green}(directory)${NC}"
    fi
    echo -e "${Yellow}${win_rel}${NC}\n  ${local_path}${suffix}"
  done
}

# Global flag parsing
FORCE_FLAG=""
ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
  -f | --force)
    FORCE_FLAG="-f"
    shift
    ;;
  *)
    ARGS+=("$1")
    shift
    ;;
  esac
done

# Re-set positional parameters without the flags
set -- "${ARGS[@]}"

# Subcommand Router
case "${1:-}" in
pull)
  pull "${FORCE_FLAG}" "${2:-}"
  ;;
push)
  push "${FORCE_FLAG}" "${2:-}"
  ;;
list)
  list
  ;;
*)
  echo "Usage: $0 {push|pull|list} [filter]"
  echo "Examples:"
  echo "  $0 push glzr"
  echo "  $0 pull keyboard"
  echo "  $0 list"
  echo ""
  list
  exit 1
  ;;
esac
