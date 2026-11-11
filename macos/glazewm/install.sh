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
  sleepwatcher
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

# Runs glazewm-wake on system wakeup (-w) and display wakeup (-W): waking
# from system sleep sends only the first. Written rather than stowed, because
# launchd needs absolute paths and may skip a symlinked plist.
label=com.github.gelio.glazewm-wake
plist="$HOME/Library/LaunchAgents/$label.plist"
mkdir -p "$(dirname "$plist")"
cat >"$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>$(brew --prefix)/sbin/sleepwatcher</string>
    <string>-V</string>
    <string>-w</string>
    <string>$HOME/.local/bin/glazewm-wake</string>
    <string>-W</string>
    <string>$HOME/.local/bin/glazewm-wake</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$plist"

if ((${#failed_casks[@]})); then
  echo "# Casks not installed: ${failed_casks[*]}"
fi

echo "Open GlazeWM and grant it Accessibility in System Settings → Privacy & Security."
