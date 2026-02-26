#!/usr/bin/env bash
set -euo pipefail

# Symlink notification scripts into ~/.claude/
stow -v --no-folding -R -t "$HOME" stowed

# Merge hooks config into ~/.claude/settings.json
node --experimental-strip-types setup-hooks.ts
