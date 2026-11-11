#!/usr/bin/env bash
set -euo pipefail

# macOS binds Ctrl+Space and Ctrl+Option+Space to switching input sources and
# swallows them even with a single input source, so they never reach the
# terminal (blink.cmp's <C-Space> in Neovim).
#
# AppleSymbolicHotKeys entries:
#   60: Select the previous input source (Ctrl+Space)
#   61: Select next source in Input menu (Ctrl+Option+Space)
# The parameters are the shortcut's character code (32, space), key code
# (49, space) and modifier flags (Ctrl 262144, Option 524288). Keeping them
# lets the shortcut be turned back on in System Settings.

disable_hotkey() {
  local id=$1 modifiers=$2
  defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add "$id" "
    <dict>
      <key>enabled</key><false/>
      <key>value</key>
      <dict>
        <key>parameters</key>
        <array><integer>32</integer><integer>49</integer><integer>$modifiers</integer></array>
        <key>type</key><string>standard</string>
      </dict>
    </dict>"
}

disable_hotkey 60 262144
disable_hotkey 61 786432

# Applies the change without logging out. It can exit 0 even when it fails
# (for example "CGSSetSymbolicHotKeyValue(60, …) failed" without access to the
# window server), so check its output too.
activate_settings=/System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings
if [[ -x $activate_settings ]] &&
  output=$("$activate_settings" -u 2>&1) &&
  [[ $output != *failed* ]]; then
  exit 0
fi
[[ -n ${output:-} ]] && echo "$output"
echo "# Log out and back in to free Ctrl+Space"
