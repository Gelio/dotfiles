#!/usr/bin/env bash
set -euo pipefail

# Installs tpm and the plugins listed in ~/.tmux.conf. Safe to re-run:
# install_plugins skips plugins that are already installed.
tpm_dir="$HOME/.tmux/plugins/tpm"

if [[ ! -d "$tpm_dir" ]]; then
  git clone --depth 1 https://github.com/tmux-plugins/tpm "$tpm_dir"
fi

"$tpm_dir/bin/install_plugins"
