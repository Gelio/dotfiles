---
name: update-neovim
description: Use when the user asks to update, upgrade, build, or install Neovim from source
---

# Update Neovim

## Overview

Builds and installs Neovim from source using the local `install.sh` script. Every machine and CI build the one commit stored in `universal/neovim/neovim-commit`. The script clones or updates the Neovim repo at `~/.local/neovim`, checks out that commit, builds it, and stows config files.

Upgrading means bumping that file. `install.sh` alone only brings a machine to the commit already pinned.

## When to Use

- User asks to update/upgrade Neovim
- User wants to rebuild Neovim from source
- User wants to do a clean build of Neovim

## Steps

To upgrade, bump the pin first. To only install or rebuild the pinned commit, skip to step 2.

1. Store the full SHA of the new commit (the tip of `master` unless the user names one):

```bash
git ls-remote https://github.com/neovim/neovim.git refs/heads/master | cut -f1 > universal/neovim/neovim-commit
```

2. Run the install script from the neovim dotfiles directory:

```bash
cd universal/neovim && ./install.sh
```

3. After an upgrade, list what changed between the old and new pin, and summarize it for the user:

```bash
git -C ~/.local/neovim log --oneline <old-commit>..<new-commit>
```

4. Commit the changed `neovim-commit` on a branch and open a PR. The `Neovim` workflow builds the new commit and checks that the config starts on it.

## Script Flags

| Flag | Description |
|------|-------------|
| `-c` / `--clean` | Run `make distclean` before building |
| `--skip-pull` | Don't fetch or check out the pinned commit, build from current state |

Use `--clean` when a build fails due to stale artifacts. Use `--skip-pull` to rebuild the current checkout, for example to try a commit before pinning it.

## What the Script Does

1. Navigates to `~/.local/neovim` (clones if missing)
2. Fetches and checks out the commit in `neovim-commit` (unless `--skip-pull`)
3. Fixes ownership (`sudo chown -R $USER .`)
4. Builds with `make CMAKE_BUILD_TYPE=RelWithDebInfo`
5. Installs with `sudo make install`
6. Stows config files via `./stow.sh`

## Common Issues

- **Build permission errors**: The script already handles this with `sudo chown -R`. If it persists, use `--clean`.
- **Checkout fails**: Local changes in `~/.local/neovim` block switching to the pinned commit. Look at them with `git status` there before discarding anything.
- **Build fails**: Try `--clean` flag to do a fresh build.
