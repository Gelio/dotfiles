#!/usr/bin/env bash
set -euo pipefail

formulae=(
  koekeishiya/formulae/yabai
  koekeishiya/formulae/skhd
  FelixKratz/formulae/sketchybar
)

echo "# Installing formulae"
echo "${formulae[@]}"
brew install ${formulae[@]}

# NOTE: cargo comes from mise, so run universal/bootstrap.sh first
cargo install --git https://github.com/Gelio/yabaictl

stow -v --no-folding -t "$HOME" --adopt stowed

skhd --start-service

yabai_symlink=/usr/local/bin/yabai
if [[ ! -f "$yabai_symlink" ]]; then
  sudo ln -s /opt/homebrew/bin/yabai $yabai_symlink
fi

echo "Run ./setup-yabai.sh to load the scripting addition (needs SIP partially disabled) and start yabai."
