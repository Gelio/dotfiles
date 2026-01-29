#!/usr/bin/env bash
set -euo pipefail

cargo binstall mise
./stow.sh

# Necessary for CLI completions to work
mise use -g usage
