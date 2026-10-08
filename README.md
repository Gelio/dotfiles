# Personal dotfiles and configuration files

A list of my personal dotfiles, configuration files, and scripts that install
various applications.

## Universal tools (mise)

CLI tools and their config files are managed by [mise](https://mise.jdx.dev).

```bash
universal/bootstrap.sh            # installs mise, tools and their dotfiles
universal/bootstrap.sh --dry-run  # preview
```

If mise is missing, `bootstrap.sh` downloads a pinned release binary from GitHub and
installs it only if its SHA-256 matches the hash in the script. To bump the pin, update
`mise_version` and the four hashes from that release's `SHASUMS256.txt`.

`universal/mise/config/` is linked to `~/.config/mise`:

- `config.toml`: tools and dotfiles every machine gets.
- `config.<group>.toml`: optional groups (`git`, `fs`, `sys`, `lang`, `ai`, `work`).
  Enable them per machine in the gitignored `miserc.toml`, e.g. `env = ["git", "fs"]`,
  then re-run `bootstrap.sh`.
- `config.local.toml`: gitignored, holds this machine's `dotfiles.root`.

Each tool keeps its config files in `universal/<tool>/home/`, which mirrors `~`, and is
linked by a `[dotfile_groups.<tool>]` entry. Files are linked one by one, so directories
like `~/.local/bin` can hold other files too. A directory that only the tool uses, like
`~/.config/lazygit`, is linked as a whole through the group's `entries`, so files the
tool creates there land in the repo. Turning a group off later does not remove its
links; run `mise bootstrap dotfiles unapply <target>` for that.

Upgrade tools with `mise upgrade` and mise itself with `mise self-update`.

### Moving an existing machine from stow

Machines set up with the old per-tool `stow.sh` scripts have leftovers that break the
first `bootstrap.sh` run or new shells:

```bash
# Dangling stow links. mise replaces the others, but the renamed shell snippets
# (50-mise, 10-rust) and ~/.config/mise/config.toml are left behind
find ~/.bashrc.d ~/.zshrc.d ~/.config/mise -xtype l -print -delete
# Old stow created a real directory here; bootstrap.sh needs it free for its symlink
rmdir ~/.config/mise
# git/install.sh appended this include without the markers mise now manages it with.
# Your git identity is in that file, so run bootstrap.sh right after
git config --global --unset-all include.path '^~/\.config/git\.gitconfig$'
# Agent skills, hooks and scripts were stowed from universal/agents/stowed, now home/.
# Only links into that directory; other links in ~/.local/bin stay
find ~/.agents ~/.claude ~/.codex ~/.local/bin -type l -lname '*/agents/stowed/*' -print -delete
# Old copies that would shadow the mise ones outside interactive shells
cargo install --list   # uninstall the ones now in universal/mise/config/*.toml
ls ~/go/bin            # remove lazygit, lazydocker, gotop
```

Directories mise now links as a whole (`~/.config/lazygit`, `~/.config/kitty`, ...) may
still be real directories or old stow links. `bootstrap.sh` moves them to
`<dir>.pre-mise-<timestamp>` before linking; delete those once you've checked them.

An older mise is fine as long as it is at least the pinned version; otherwise run
`mise self-update` first. `bootstrap.sh` checks this.

The terminal emulators (ghostty, kitty, wezterm) are not installed by mise, but their
config is linked by it anyway. Neovim keeps its own `install.sh`/`stow.sh` scripts and
`stowed/` folder.
