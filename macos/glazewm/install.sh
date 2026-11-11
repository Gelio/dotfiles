#!/usr/bin/env bash
set -euo pipefail

# Allows running the script from any directory
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
pushd "$script_dir" >/dev/null

casks=(
  glzr-io/tap/glazewm
  glzr-io/tap/zebar
)

formulae=(
  FelixKratz/formulae/borders
)

echo "# Installing formulae"
echo "${formulae[@]}"
brew install "${formulae[@]}"

echo "# Installing casks"
echo "${casks[@]}"
brew install --cask "${casks[@]}"

stow -v --no-folding -t "$HOME" --adopt stowed

echo "Open GlazeWM and grant it Accessibility in System Settings → Privacy & Security."
