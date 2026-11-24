# macOS

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

## Window managers

[GlazeWM](glazewm/README.md) is the default tiling window manager, with Zebar
and JankyBorders. It doesn't need SIP disabled.

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
