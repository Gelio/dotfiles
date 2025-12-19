#!/usr/bin/env bash

layout="N/A"
if [ "$SENDER" == "space_change" ]; then
  layout=$(yabai -m query --spaces --space "$SID" | jq -r '.type')
elif [ "$SENDER" == "display_change" ]; then
  layout=$(yabai -m query --spaces --display "$INFO" | jq -r 'map(select(.["is-visible"] == true)).[0].type')
else
  # The script was invoked by a yabai signal
  layout=$(yabai -m query --spaces | jq -r 'map(select(.["is-visible"] == true and .["has-focus"] == true)).[0].type')
fi

if [ -z "$NAME" ]; then
  # If invoked directly, use a default name
  NAME="space_layout"
fi

sketchybar --set "$NAME" label="$layout"
