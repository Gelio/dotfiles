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
linked by a `[dotfile_groups.<tool>]` entry. Turning a group off later does not remove
its links; run `mise bootstrap dotfiles unapply <target>` for that.

Upgrade tools with `mise upgrade` and mise itself with `mise self-update`.

Tools not installed by mise (neovim, ghostty, kitty, wezterm) keep their own
`install.sh`/`stow.sh` scripts and `stowed/` folders.
