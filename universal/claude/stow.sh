#!/usr/bin/env bash
set -euo pipefail

# Create directories so stow does not fold them
mkdir -p "$HOME/.agents/"
mkdir -p "$HOME/.claude/skills/"
mkdir -p "$HOME/.claude/hooks/"

stow -v -R -t "$HOME" stowed

# Merge settings-partial.json into ~/.claude/settings.json
node --experimental-strip-types setup-settings.ts
