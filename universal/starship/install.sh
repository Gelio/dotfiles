#!/usr/bin/env bash
set -euo pipefail

cargo binstall --locked starship
./stow.sh
