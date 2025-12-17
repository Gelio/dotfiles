#!/usr/bin/env bash
set -euo pipefail

stow -v --no-folding -t "$HOME" --adopt stowed
