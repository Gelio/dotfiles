#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Label spaces using stable indexes
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🛩
# @raycast.packageName yabaictl

set -e

YABAICTL_PATH="$HOME/.cargo/bin/yabaictl"

$YABAICTL_PATH label-spaces
