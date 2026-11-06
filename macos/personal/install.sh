#!/usr/bin/env bash
set -euo pipefail

casks=(
  bitwarden
  rambox
)

echo "# Installing casks"
echo "${casks[@]}"
brew install --cask --adopt ${casks[@]}
