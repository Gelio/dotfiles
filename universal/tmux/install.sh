#!/usr/bin/env bash
set -euo pipefail

echo "> For tmux bottom bar to work correctly, powerline icons are required"
echo "> Install a NerdFond like FiraCode NF or JetBrains Mono NF"

printf "\n\n"

[[ ! -d ~/.tmux/plugins/tpm ]] && git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
echo "> Do 'Ctrl + b I' in tmux to install the plugins"
