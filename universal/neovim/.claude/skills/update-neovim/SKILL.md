---
name: update-neovim
description: Use when the user asks to update, upgrade, build, or install Neovim from source
---

# Update Neovim

## Overview

Builds and installs Neovim from source using the local `install.sh` script. The script clones or updates the Neovim repo at `~/.local/neovim`, builds it, and stows config files.

## When to Use

- User asks to update/upgrade Neovim
- User wants to rebuild Neovim from source
- User wants to do a clean build of Neovim

## Steps

1. Run the install script from the neovim dotfiles directory:

```bash
cd /Users/grzegorz.rozdzialik/ubuntu-dotfiles/universal/neovim && ./install.sh
```

2. After the build completes, check what changed since the last pull:

```bash
cd ~/.local/neovim && git log '@{1}..' --oneline
```

3. Summarize the changes for the user.

## Script Flags

| Flag | Description |
|------|-------------|
| `-c` / `--clean` | Run `make distclean` before building |
| `--skip-pull` | Skip `git pull`, build from current state |

Use `--clean` when a build fails due to stale artifacts. Use `--skip-pull` to rebuild at the current commit without updating.

## What the Script Does

1. Navigates to `~/.local/neovim` (clones if missing)
2. Pulls latest changes (unless `--skip-pull`)
3. Fixes ownership (`sudo chown -R $USER .`)
4. Builds with `make CMAKE_BUILD_TYPE=RelWithDebInfo`
5. Installs with `sudo make install`
6. Stows config files via `./stow.sh`

## Common Issues

- **Build permission errors**: The script already handles this with `sudo chown -R`. If it persists, use `--clean`.
- **Pull fails**: Normal when a specific commit hash is checked out instead of a branch. The script continues anyway.
- **Build fails**: Try `--clean` flag to do a fresh build.
