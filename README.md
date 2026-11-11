# Personal dotfiles and configuration files

A list of my personal dotfiles, configuration files, and scripts that install
various applications.

The Ubuntu install scripts and i3 desktop config that lived in `ubuntu/` have
been removed. Commit `6651c717` is the last one that changed them, so
`git ls-tree -r --name-only 6651c717 -- ubuntu/` lists them and
`git restore --source=6651c717 -- ubuntu/` brings them back.
`git log -- ubuntu/` shows their history.

## Universal tools (mise)

CLI tools and their config files are managed by [mise](https://mise.jdx.dev).

```bash
universal/bootstrap.sh            # installs mise, tools and their dotfiles
universal/bootstrap.sh --dry-run  # preview what mise would change
```

`--dry-run` only previews `mise bootstrap`. The script still installs mise if
it's missing, links `~/.config/mise`, writes `config.local.toml` and
`miserc.toml` if they're missing, and installs `jq`. It prints this list when it
starts.

Other arguments go to `mise bootstrap`. Passing `--only` or `--skip` replaces
the default `--only dotfiles,tools`, so `universal/bootstrap.sh --only dotfiles`
links dotfiles without installing tools.

If mise is missing, `bootstrap.sh` downloads a pinned release binary from GitHub
and installs it only if its SHA-256 matches the hash in the script. To bump the
pin, update `mise_version` and the four hashes from that release's
`SHASUMS256.txt`.

`universal/mise/config/` is linked to `~/.config/mise`:

- `config.toml`: tools and dotfiles every machine gets.
- `config.<group>.toml`: optional groups (`git`, `fs`, `sys`, `lang`, `ai`,
  `work`, `personal`). Enable them per machine in the gitignored `miserc.toml`.
  If it's missing, `bootstrap.sh` asks which groups to enable, with `git`, `fs`,
  `sys` and `ai` preselected, and uses those without asking when there's no
  terminal. To change them later, edit the file and re-run `bootstrap.sh`.
- `config.local.toml`: gitignored, holds this machine's `dotfiles.root`.

Each tool keeps its config files in `universal/<tool>/home/`, which mirrors `~`,
and is linked by a `[dotfile_groups.<tool>]` entry. Files are linked one by one,
so directories like `~/.local/bin` can hold other files too. A directory that
only the tool uses, like `~/.config/lazygit`, is linked as a whole through the
group's `entries`, so files the tool creates there land in the repo. Turning a
group off later does not remove its links; run
`mise bootstrap dotfiles unapply <target>` for that.

Upgrade tools with `mise upgrade` and mise itself with `mise self-update`.

### Moving an existing machine from stow

Machines set up with the old per-tool `stow.sh` scripts have leftovers that
break the first `bootstrap.sh` run or new shells:

```bash
# Dangling stow links. mise replaces the others, but the renamed shell snippets
# (50-mise, 10-rust) and ~/.config/mise/config.toml are left behind
find ~/.bashrc.d ~/.zshrc.d ~/.config/mise -xtype l -print -delete
# Old stow created a real directory here; bootstrap.sh needs it free for its symlink
rmdir ~/.config/mise
# git/install.sh appended this include without the markers mise now manages it with.
# Your git identity is in that file, so run bootstrap.sh right after
git config --global --unset-all include.path '^~/\.config/git\.gitconfig$'
# The old Ubuntu setup appended a loop sourcing ~/.bashrc.d without markers. mise now
# adds its own copy, so delete the old one from ~/.bashrc or snippets load twice
grep -n -A2 'for file in ~/.bashrc.d' ~/.bashrc
# Same for the line macos/core/install-zsh.sh appended to ~/.zshrc. The mise block
# now sources ~/.zshrc-dotfiles itself, so delete the old line
grep -n 'source ~/.zshrc-dotfiles' ~/.zshrc
# Agent skills, hooks and scripts were stowed from universal/agents/stowed, now home/.
# Only links into that directory; other links in ~/.local/bin stay
find ~/.agents ~/.claude ~/.codex ~/.local/bin -type l -lname '*/agents/stowed/*' -print -delete
# Old copies that would shadow the mise ones outside interactive shells
cargo install --list   # uninstall the ones now in universal/mise/config/*.toml
ls ~/go/bin            # remove lazygit, lazydocker, gotop
```

Directories mise now links as a whole (`~/.config/lazygit`, `~/.config/kitty`,
...) may still be real directories or old stow links. `bootstrap.sh` moves them
to `<dir>.pre-mise-<timestamp>` before linking; delete those once you've checked
them.

An older mise is fine as long as it is at least the pinned version; otherwise
run `mise self-update` first. `bootstrap.sh` checks this.

The terminal emulators (ghostty, kitty, wezterm) are not installed by mise, but
their config is linked by it anyway. Neovim keeps its own `install.sh`/`stow.sh`
scripts and `stowed/` folder.

## macOS

Run this before `universal/bootstrap.sh`. mise needs the Xcode Command Line
Tools to build the `cargo:` tools. They usually come from macOS's prompt when
`git` first runs, and Homebrew's installer installs them otherwise:

```bash
cd macos/core && ./install-all.sh  # Homebrew if missing, apps, core config and settings
```

Raycast's script directories aren't set by a script. In Raycast's settings,
under Extensions, add `macos/raycast/scripts` as a script directory.

`install-all.sh` also turns off the input source shortcuts (Ctrl+Space and
Ctrl+Option+Space), so Ctrl+Space reaches the terminal. Turn them back on in
System Settings → Keyboard → Keyboard Shortcuts → Input Sources.

Bitwarden and Rambox are optional, for personal Macs:

```bash
cd macos/personal && ./install.sh
```

GlazeWM tiles windows with the same bindings as on Windows, plus Zebar for the
bar and JankyBorders for focus borders. It doesn't need SIP disabled:

```bash
cd macos/glazewm && ./install.sh  # installs them, links GlazeWM's config
```

Then open GlazeWM and grant it Accessibility. Its bindings use Left Option only,
so Right Option still types Polish letters. GlazeWM can't tell the two Option
keys apart, so while it runs, Karabiner turns Left Option+key into
Option+Command+key, and GlazeWM binds those.

yabai, skhd and SketchyBar are optional, because they depend on each other and
yabai's scripting addition needs SIP partially disabled:

```bash
cd macos/yabai && ./install.sh     # installs them and yabaictl, links their config
./setup-yabai.sh                   # loads the scripting addition, starts yabai
```

To use their Raycast scripts, add `macos/yabai/raycast/scripts` to Raycast's
script directories.

Macs set up before these moved out of `macos/core` have dangling links to them.
Delete those first, on Macs that skip yabai too:

```bash
find ~/.config/yabai ~/.config/skhd ~/.config/sketchybar -type l ! -exec test -e {} \; -print -delete
```
