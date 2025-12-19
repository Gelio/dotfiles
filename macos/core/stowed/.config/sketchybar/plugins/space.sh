#!/usr/bin/env bash

# The $SELECTED variable is available for space components and indicates if
# the space invoking this script (with name: $NAME) is currently selected:
# https://felixkratz.github.io/SketchyBar/config/components#space----associate-mission-control-spaces-with-an-item

space=$(yabai -m query --spaces --space "$SID")
label=$(echo "$space" | jq -r '.label')
if [ -z "$label" ]; then
  label=$(echo "$space" | jq -r '.index')
fi

sketchybar --set "$NAME" background.drawing="$SELECTED" icon="$label"

# By default, SketchyBar only updates the space that triggered the script.
# For more consistency with yabai, let's update all spaces.
PLUGIN_DIR="$CONFIG_DIR/plugins"
"$PLUGIN_DIR"/update_all_spaces.sh
