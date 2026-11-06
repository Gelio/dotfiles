#!/usr/bin/env bash
set -euo pipefail

casks=(
  firefox
  karabiner-elements
  obsidian
  kitty
  wezterm@nightly
  raycast
  kap
  obs
  handy
  linearmouse
  hovancik/stretchly/stretchly
  font-jetbrains-mono-nerd-font
)

formulae=(
  stow
  tmux
  findutils
  wget
  highlight
  thaw
  pkg-config
  git
)

echo "# Installing formulae"
echo "${formulae[@]}"
brew install ${formulae[@]}

echo "# Installing casks"
echo "${casks[@]}"
brew install --cask --adopt ${casks[@]}

# https://hovancik.net/stretchly/downloads/
sudo xattr -r -d com.apple.quarantine /Applications/Stretchly.app

# NOTE: used for completions files
mkdir -p ~/.zfunc/
