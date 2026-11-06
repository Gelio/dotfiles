#!/usr/bin/env bash
set -euo pipefail

# https://github.com/koekeishiya/yabai/wiki/Installing-yabai-(latest-release)#configure-scripting-addition
echo "$(whoami) ALL=(root) NOPASSWD: sha256:$(shasum -a 256 "$(which yabai)" | cut -d " " -f 1) $(which yabai) --load-sa" | sudo tee /private/etc/sudoers.d/yabai

echo "You will get a prompt to enable Yabai in macOS accessibility settings."
echo "If yabai does not restart, you need to run this script again after changing those accessibility settings."
set -x
yabai --restart-service

# Re-apply all rules after restart, but give it a few seconds to settle
sleep 4
yabai -m rule --apply
