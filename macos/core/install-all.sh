#!/usr/bin/env bash
set -euo pipefail

if [[ ! -x /opt/homebrew/bin/brew ]]; then
  # https://brew.sh/
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
eval "$(/opt/homebrew/bin/brew shellenv)"

./brew-install.sh
./stow.sh
