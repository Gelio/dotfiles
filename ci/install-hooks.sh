#!/usr/bin/env bash
# Registers this repo's git hooks in its local config, which all of its worktrees
# share. Safe to re-run.
set -euo pipefail

ci_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$ci_dir/.."

# Runs the same checks as CI before commits reach the public remote, mainly so
# that a secret is caught before it is exposed. CI stays the real enforcement,
# so a machine that is still bootstrapping can push without mise. It's a function
# because git appends "$@" to the command, which is a syntax error after `fi`.
lint_command='lint() { if command -v mise >/dev/null; then mise run lint; else echo "dotfiles-lint: mise is missing, skipping the checks" >&2; fi; }; lint'

git config --local --replace-all hook.dotfiles-lint.event pre-push
git config --local --replace-all hook.dotfiles-lint.command "$lint_command"

# Older git ignores these keys without any error
if [[ "$(git hook list pre-push 2>/dev/null)" != *dotfiles-lint* ]]; then
  echo "dotfiles-lint isn't registered: config-based hooks need git 2.54+" >&2
  exit 1
fi
echo "Installed the dotfiles-lint pre-push hook"
