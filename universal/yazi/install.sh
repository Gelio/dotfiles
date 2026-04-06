#!/usr/bin/env bash
set -euo pipefail

cargo binstall yazi-fm

stow --target="$HOME" -v --no-folding stowed
