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
brew install "${formulae[@]}"

echo "# Installing casks"
echo "${casks[@]}"
# NOTE: one at a time, because a cask fails if its app was installed outside
# Homebrew, and that should not stop the rest of the setup
failed_casks=()
for cask in "${casks[@]}"; do
  brew install --cask "$cask" || failed_casks+=("$cask")
done

# https://hovancik.net/stretchly/downloads/
if [[ -d /Applications/Stretchly.app ]]; then
  sudo xattr -r -d com.apple.quarantine /Applications/Stretchly.app
fi

# NOTE: used for completions files
mkdir -p ~/.zfunc/

if ((${#failed_casks[@]})); then
  echo "# Casks not installed: ${failed_casks[*]}"
fi
