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

stable_index=""
if [[ -n "$1" ]]; then
  stable_index="--stable-index $1"
fi

description=""
if [[ -n "$2" ]]; then
  description="--description $2"
fi

$YABAICTL_PATH set-label $stable_index $description
