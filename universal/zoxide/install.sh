#!/usr/bin/env bash

set -euo pipefail

# https://github.com/ajeetdsouza/zoxide
cargo install zoxide

stow -v --no-folding -t "$HOME" stowed
echo "Reload your shell for zoxide to take effect"
