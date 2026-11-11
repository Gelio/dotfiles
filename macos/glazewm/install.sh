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
# NOTE: one at a time, because a cask fails if its app was installed outside
# Homebrew, and that should not stop the config from being linked
failed_casks=()
for cask in "${casks[@]}"; do
  brew install --cask "$cask" || failed_casks+=("$cask")
done

# NOTE: no --adopt: GlazeWM writes a default config on first launch, and
# adopting it would replace this repo's config. Stow reports it as a
# conflict instead; delete ~/.glzr/glazewm/config.yaml and rerun.
stow -v --no-folding -t "$HOME" stowed

if ((${#failed_casks[@]})); then
  echo "# Casks not installed: ${failed_casks[*]}"
fi

echo "Open GlazeWM and grant it Accessibility in System Settings → Privacy & Security."
