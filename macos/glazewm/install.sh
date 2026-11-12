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

# Zebar uses the Windows aurora pack, whose bar-macos widget shows only
# GlazeWM's state. The pack's files are linked one by one into a real folder,
# in case Zebar skips a linked pack folder when it looks for packs.
zebar_dir="$HOME/.glzr/zebar"
pack=sakyasumedh.aurora@1.0.0-modified
pack_src="$(cd -- "$script_dir/../../windows/config/.glzr/zebar/$pack" && pwd)"
mkdir -p "$zebar_dir/$pack"
for f in "$pack_src"/*; do
  ln -sfn "$f" "$zebar_dir/$pack/"
done
# Zebar writes its own settings.json on first launch, starting its starter bar.
settings="$zebar_dir/settings.json"
if [[ -f "$settings" && ! -L "$settings" ]]; then
  mv "$settings" "$settings.bak"
  echo "# Moved Zebar's own settings.json to $settings.bak"
fi
ln -sfn "$script_dir/zebar/settings.json" "$settings"

# Removes the LaunchAgents and scripts of an earlier version of this module.
for old in glazewm-karabiner-sync glazewm-wake; do
  old_plist="$HOME/Library/LaunchAgents/com.github.gelio.$old.plist"
  if [[ -f "$old_plist" ]]; then
    launchctl bootout "gui/$(id -u)/com.github.gelio.$old" 2>/dev/null || true
    rm "$old_plist"
  fi
  # Stow leaves links to removed files behind.
  if [[ -L "$HOME/.local/bin/$old" && ! -e "$HOME/.local/bin/$old" ]]; then
    rm "$HOME/.local/bin/$old"
  fi
done

# One LaunchAgent runs glazewm-helper at login and keeps it running. It's
# written rather than stowed, because launchd needs absolute paths and may skip
# a symlinked plist. Endpoint security on a managed Mac can flag writing and
# loading a LaunchAgent, so this only happens when the plist changes or the
# agent isn't loaded.
label=com.github.gelio.glazewm-helper
plist="$HOME/Library/LaunchAgents/$label.plist"
new_plist=$(
  cat <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$label</string>
  <key>ProgramArguments</key>
  <array>
    <string>$HOME/.local/bin/glazewm-helper</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardErrorPath</key>
  <string>$HOME/Library/Logs/$label.log</string>
</dict>
</plist>
EOF
)
if [[ "$(cat "$plist" 2>/dev/null)" == "$new_plist" ]] &&
  launchctl print "gui/$(id -u)/$label" >/dev/null 2>&1; then
  echo "# $label is up to date"
else
  mkdir -p "$(dirname "$plist")" "$HOME/Library/Logs"
  printf '%s\n' "$new_plist" >"$plist"
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  # bootout returns before the old service is gone, and bootstrap fails until
  # it is, so retry for a few seconds.
  tries=0
  until launchctl bootstrap "gui/$(id -u)" "$plist"; do
    ((++tries < 5)) || exit 1
    sleep 1
  done
  echo "# $label (re)loaded"
fi

if ((${#failed_casks[@]})); then
  echo "# Casks not installed: ${failed_casks[*]}"
fi

echo "Open GlazeWM and grant it Accessibility in System Settings → Privacy & Security (on macOS 27: Device Control and Data Access)."
