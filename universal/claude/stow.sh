#!/usr/bin/env bash
set -euo pipefail

stow -v -R -t "$HOME" stowed

# Merge settings-partial.json into ~/.claude/settings.json
node --experimental-strip-types setup-settings.ts
