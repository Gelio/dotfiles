#!/usr/bin/env bash
set -euo pipefail

# Control+Command+drag anywhere in a window moves it, not only its title bar.
# Apps read the setting when they start, so restart them (or log out) to pick
# it up. Turn it off with: defaults delete -g NSWindowShouldDragOnGesture

defaults write -g NSWindowShouldDragOnGesture -bool true
