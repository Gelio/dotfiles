#!/usr/bin/env bash
set -euo pipefail

if ! command -v gsudo >/dev/null; then
  echo "gsudo is required to create config symlinks. Installing it now."
  winget.exe install gsudo
  echo "Restart WSL terminal for gsudo to be available"
  exit 1
fi

winget.exe install GlazeWM --exact

distro_name="$WSL_DISTRO_NAME"
if [[ -z "$distro_name" ]]; then
  echo "Unable to install GlazeWM config. Linux distro name cannot be detected."
  exit 1
fi

echo "Detected Linux distro name: $distro_name"

glazewm_config_path=$(realpath ./config/.glzr/glazewm/config.yaml)
if [[ ! -f "$glazewm_config_path" ]]; then
  echo "Unable to locate GlazeWM config in dotfiles under $glazewm_config_path"
  exit 1
fi

# zebar_settings_path=$(realpath ./config/.glzr/zebar/settings.json)
# if [[ ! -f "$zebar_settings_path" ]]; then
#   echo "Unable to locate Zebar settings in dotfiles under $zebar_settings_path"
#   exit 1
# fi

windows_userprofile_path=$(cmd.exe /c 'echo %USERPROFILE%' 2>/dev/null | tr -d '\r')
if [[ -z "$windows_userprofile_path" ]]; then
  echo "Unable to find Windows USERPROFILE path"
  exit 1
fi

echo "Windows USERPROFILE: $windows_userprofile_path"

link_wsl_file() {
  declare -r file="$1"
  if [[ ! -f "$file" ]]; then
    echo "Path $file is not a regular file"
    exit 1
  fi

  declare -r windows_dir="$2"
  if [[ -z "$windows_dir" ]]; then
    echo "Windows dir is empty"
    exit 1
  fi

  pushd /tmp >/dev/null
  windows_path_abs="$windows_dir\\$(wslpath -w "$file")"
  popd >/dev/null

  wsl_file_path_abs=$(wslpath -aw "$file")

  echo "Creating link: $windows_path_abs -> $wsl_file_path_abs"
  pushd "$(wslpath "$windows_userprofile_path")" >/dev/null
  set -x
  mkdir -p "$(dirname "$file")"
  gsudo powershell.exe -Command "New-Item -ItemType SymbolicLink -Path \"$windows_path_abs\" -Target \"\\\\$wsl_file_path_abs\""
  popd
}

pushd config >/dev/null
link_wsl_file ".glzr/glazewm/config.yaml" "$windows_userprofile_path"
