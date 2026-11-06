#!/usr/bin/env bash
set -euo pipefail

casks=(
  bitwarden
  firefox
  karabiner-elements
  rambox
  obsidian
  kitty
  aldente
  raycast
  kap
  obs
  linearmouse
  hovancik/stretchly/stretchly
)

formulae=(
  go
  stow
  tmux
  findutils
  wget
  gnupg
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
brew install --cask ${casks[@]}

# https://hovancik.net/stretchly/downloads/
sudo xattr -r -d com.apple.quarantine /Applications/Stretchly.app

# NOTE: used for completions files
mkdir -p ~/.zfunc/

go install github.com/Gelio/go-global-update@latest
