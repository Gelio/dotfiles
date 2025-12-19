#!/usr/bin/env bash

spaces=$(yabai -m query --spaces)
spaces_parsed=$(jq -r '.[] | "\(.index),\(.["is-visible"]),\(.label)"' <<<"$spaces")

while IFS=, read -r index visible label; do
  if [ -z "$label" ]; then
    label=$index
  fi

  sketchybar --set "space.$index" background.drawing="$visible" icon="$label"
done <<<"$spaces_parsed"
