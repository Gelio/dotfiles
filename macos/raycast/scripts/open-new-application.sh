#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Open new application
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🛩
# @raycast.packageName Applications
# @raycast.argument1 { "type": "text", "placeholder": "application name" }

set -e

open -n -a "$1"
