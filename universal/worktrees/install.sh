#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install dependencies (zx). npm ci if a lockfile exists, else npm install.
if [ -f "$HERE/package-lock.json" ]; then
  npm --prefix "$HERE" ci
else
  npm --prefix "$HERE" install
fi

# mkdir only the PARENTS — never the worktrees dir itself, or the dir symlink
# below would nest inside it instead of replacing it.
mkdir -p "$HOME/.local/bin" "$HOME/.local/share"

# Stable anchor: the whole project at ~/.local/share/worktrees. Everything
# (types, README, bin) hangs off this one home-dir location, so relocating the
# dotfiles checkout only means re-running install.sh. `-n` re-points an existing
# dir symlink cleanly instead of dereferencing into it.
ln -sfn "$HERE" "$HOME/.local/share/worktrees"

# The command: a symlink to the TS entry. Node resolves the realpath (-> the
# repo), strips types, and loads the rest of the project via relative imports.
ln -sfn "$HERE/bin/worktrees.ts" "$HOME/.local/bin/worktrees"

# Shell completions. zsh: ~/.zfunc is already on $fpath + compinit autoloads
# _worktrees. bash: ~/.local/share/bash-completion/completions is the standard
# per-command autoload dir. Both are symlinks, so edits track the checkout.
mkdir -p "$HOME/.zfunc" "$HOME/.local/share/bash-completion/completions"
ln -sfn "$HERE/completions/_worktrees" "$HOME/.zfunc/_worktrees"
ln -sfn "$HERE/completions/worktrees.bash" "$HOME/.local/share/bash-completion/completions/worktrees"

echo "Installed: $HOME/.local/bin/worktrees -> $HERE/bin/worktrees.ts"
echo "Project:   $HOME/.local/share/worktrees -> $HERE"
echo "Types at:  $HOME/.local/share/worktrees/src/types.ts (for repo configs)"
echo "Completions: zsh -> ~/.zfunc/_worktrees, bash -> ~/.local/share/bash-completion/completions/worktrees"
