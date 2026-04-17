#!/usr/bin/env bash
set -euo pipefail

# Symlink hooks
stow -v -R -t "$HOME" stowed

# Symlink skills into ~/.claude/skills/
stow -v -R -t "$HOME/.claude/skills" skills

# Merge settings-partial.json into ~/.claude/settings.json
node --experimental-strip-types setup-settings.ts
