#!/usr/bin/env bash
set -euo pipefail

stow --no-folding -v -R -t "$HOME" stowed-wsl
