#!/usr/bin/env bash
set -euo pipefail

if ! grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
  echo "> WezTerm installation is only supported on Windows (WSL)" >&2
  exit 1
fi

windows_userprofile_path=$(cmd.exe /c 'echo %USERPROFILE%' 2>/dev/null | tr -d '\r')
if [[ -z "$windows_userprofile_path" ]]; then
  echo "> Unable to find Windows USERPROFILE path" >&2
  exit 1
fi
userprofile_path=$(wslpath "$windows_userprofile_path")

# Use the nightly build. The stable release is from 2024 and has rendering
# issues on Windows (e.g. the cursor flickers when nvim redraws in tmux).
# winget's wez.wezterm.nightly cannot be used, because the installer URL always
# points to the latest nightly, so its hash never matches the manifest.
# Re-running this script updates WezTerm to the latest nightly.
winget.exe list --id Microsoft.VCRedist.2015+.x64 --exact >/dev/null ||
  winget.exe install Microsoft.VCRedist.2015+.x64 --exact

installer_path="$userprofile_path/AppData/Local/Temp/WezTerm-nightly-setup.exe"
echo "> Downloading WezTerm nightly"
curl -fSL -o "$installer_path" \
  https://github.com/wezterm/wezterm/releases/download/nightly/WezTerm-nightly-setup.exe
echo "> Installing WezTerm nightly"
"$installer_path" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
rm "$installer_path"

mise dot apply ~/.config/wezterm

# wezterm.exe runs on Windows and does not see the WSL $HOME.
# Add a stub config in the Windows home that loads the config from the WSL share.
# Windows cannot follow WSL symlinks, so point to the resolved file in this repo.
stub_path="$userprofile_path/.wezterm.lua"
config_path=$(wslpath -w "$(realpath "$HOME/.config/wezterm/wezterm.lua")")

printf 'return dofile([[%s]])\n' "$config_path" >"$stub_path"
echo "> Created $stub_path loading $config_path"
