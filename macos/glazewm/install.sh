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

# Writes a LaunchAgent that runs the given command at login and keeps it
# running, and (re)loads it. Written rather than stowed, because launchd needs
# absolute paths and may skip a symlinked plist.
install_agent() {
  local label=$1 plist arg args=""
  shift
  plist="$HOME/Library/LaunchAgents/$label.plist"
  for arg in "$@"; do
    args+="    <string>$arg</string>"$'\n'
  done
  mkdir -p "$(dirname "$plist")" "$HOME/Library/Logs"
  cat >"$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$label</string>
  <key>ProgramArguments</key>
  <array>
$args  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardErrorPath</key>
  <string>$HOME/Library/Logs/$label.log</string>
</dict>
</plist>
EOF
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  # bootout returns before the old service is gone, and bootstrap fails until
  # it is, so retry for a few seconds.
  local tries=0
  until launchctl bootstrap "gui/$(id -u)" "$plist"; do
    ((++tries < 5)) || exit 1
    sleep 1
  done
}

# Turns the Karabiner rule on while GlazeWM runs, and off while it's paused or
# not running.
install_agent com.github.gelio.glazewm-karabiner-sync \
  "$HOME/.local/bin/glazewm-karabiner-sync"

# Runs glazewm-wake on system wakeup (-w) and display wakeup (-W): waking
# from system sleep sends only the first.
install_agent com.github.gelio.glazewm-wake \
  "$(brew --prefix)/sbin/sleepwatcher" -V \
  -w "$HOME/.local/bin/glazewm-wake" \
  -W "$HOME/.local/bin/glazewm-wake"

if ((${#failed_casks[@]})); then
  echo "# Casks not installed: ${failed_casks[*]}"
fi

echo "Open GlazeWM and grant it Accessibility in System Settings → Privacy & Security (on macOS 27: Device Control and Data Access)."
