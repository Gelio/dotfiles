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
  ubersicht
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

# https://github.com/Jean-Tinland/simple-bar#installation
simple_bar_dir="$HOME/Library/Application Support/Übersicht/widgets/simple-bar"
if [[ -d "$simple_bar_dir" ]]; then
  cd "$simple_bar_dir"
  echo "Updating simple-bar"
  git pull
  cd - >/dev/null
else
  echo "Pulling simple-bar"
  git clone https://github.com/Jean-Tinland/simple-bar "$simple_bar_dir"
fi

yabai_symlink=/usr/local/bin/yabai
if [[ ! -f "$yabai_symlink" ]]; then
  sudo ln -s /opt/homebrew/bin/yabai $yabai_symlink
fi
