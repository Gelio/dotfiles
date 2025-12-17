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
)
casks_no_quarantine=(
  stretchly
  flameshot
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
  jordanbaird-ice
  pkg-config
  FelixKratz/formulae/sketchybar
)

echo "# Installing formulae"
echo "${formulae[@]}"
brew install ${formulae[@]}

echo "# Installing casks"
echo "${casks[@]}"
brew install --cask ${casks[@]}
brew install --cask --no-quarantine ${casks_no_quarantine[@]}

# NOTE: used for completions files
mkdir -p ~/.zfunc/

go install github.com/Gelio/go-global-update@latest
skhd --start-service

yabai_symlink=/usr/local/bin/yabai
if [[ ! -f "$yabai_symlink" ]]; then
  sudo ln -s /opt/homebrew/bin/yabai $yabai_symlink
fi
