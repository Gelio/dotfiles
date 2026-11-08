#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Set space label
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🛩
# @raycast.packageName yabaictl
# @raycast.argument1 { "type": "text", "placeholder": "stable-index", "optional": true }
# @raycast.argument2 { "type": "text", "placeholder": "description", "optional": true }

YABAICTL_PATH="$HOME/.cargo/bin/yabaictl"

args=(set-label)
if [[ -n "$1" ]]; then
  args+=(--stable-index "$1")
fi

if [[ -n "$2" ]]; then
  args+=(--description "$2")
fi

"$YABAICTL_PATH" "${args[@]}"
