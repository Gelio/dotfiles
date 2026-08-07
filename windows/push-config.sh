#!/usr/bin/env bash
set -euo pipefail

NC='\033[0m'
Green='\033[0;32m'

windows_username=$(powershell.exe '$env:UserName' | tr -d '\r')
echo -e "Detected Windows username: ${Green}${windows_username}${NC}"

keyboard_manager_settings_path="/mnt/c/Users/$windows_username/AppData/Local/Microsoft/PowerToys/Keyboard Manager/default.json"
echo -e "Keyboard manager settings.json path: ${Green}$keyboard_manager_settings_path${NC}"

local_settings_path=./config/keyboard-manager-settings.json

cp "$local_settings_path" "$keyboard_manager_settings_path"
echo -e "Copied keyboard manager settings"
