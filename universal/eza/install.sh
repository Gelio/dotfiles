#!/usr/bin/env bash
set -euxo pipefail

cargo binstall eza

stow -t "$HOME" --no-folding -v stowed
