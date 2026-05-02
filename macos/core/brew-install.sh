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
  stretchly
)

formulae=(
  go
  koekeishiya/formulae/yabai
  stow
  koekeishiya/formulae/skhd
  tmux
  findutils
  wget
  gnupg
  highlight
  thaw
  pkg-config
  FelixKratz/formulae/sketchybar
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
skhd --start-service

yabai_symlink=/usr/local/bin/yabai
if [[ ! -f "$yabai_symlink" ]]; then
  sudo ln -s /opt/homebrew/bin/yabai $yabai_symlink
fi
