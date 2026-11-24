# GlazeWM on macOS

GlazeWM tiles windows with mostly the same bindings as on Windows (no arrow
keys, no pause, terminal or gather-workspaces binding), plus Zebar for the bar
and JankyBorders for focus borders. It doesn't need SIP disabled. Install
`macos/core` first: the bindings depend on its Karabiner config.

```bash
cd macos/glazewm && ./install.sh  # installs them, links GlazeWM's and Zebar's config
```

Zebar uses the Windows bar's theme, but shows only workspaces, the focused
window and the tiling direction; the macOS menu bar keeps the clock, battery and
the rest. `install.sh` moves aside Zebar's own `settings.json` the first time,
to `~/.glzr/zebar/settings.json.bak`.

Then open GlazeWM and grant it Accessibility (on macOS 27: Privacy & Security →
Device Control and Data Access). If it then manages no windows, turn that toggle
off and on again.

## Bindings and Karabiner

GlazeWM's bindings use Left Option only, so Right Option still types Polish
letters. GlazeWM can't tell the two Option keys apart, so while it runs,
Karabiner turns Left Option+key into Control+Option+Command+key for the keys
GlazeWM binds, and GlazeWM binds those. Few apps use Control+Option+Command
shortcuts, so a key GlazeWM misses (before Accessibility is granted, or in a
password field) does no harm. Left Option+Control+H/J/K/L, which move a
workspace to another monitor, become Control+Option+Command+arrows, so they
don't collide with focus. The rule is off while GlazeWM isn't running. Other
Left Option combinations, like Left Option+arrows, reach apps unchanged.

Zoom's global shortcut Control+Option+Command+H (show or hide the floating
meeting controls) is the same as Left Option+H, so turn it off in Zoom's
Settings → Keyboard Shortcuts.

Karabiner doesn't notice changes to a linked `karabiner.json`, such as after a
pull. Recreate the link to make it reload:

```bash
ln -sfh "$(readlink ~/.config/karabiner/karabiner.json)" ~/.config/karabiner/karabiner.json
tail -2 /var/log/karabiner/core_service.log  # "core_configuration is updated"
```

When a change touches both the Karabiner rule and GlazeWM's bindings, update
them in an order that never has Karabiner sending a key GlazeWM doesn't bind
yet: moving to the Control+Option+Command keys, reload Karabiner first, then
GlazeWM (from its tray menu, since its reload key changes too). Going back,
reload GlazeWM first, then Karabiner. In the wrong order, Left Option+H or +M
reaches apps as Option+Command+H or +M for a moment, which hides other apps or
minimizes all windows.

## Machine-local config

GlazeWM reads a single file, so `~/.glzr/glazewm/config.yaml` is built by
`glazewm-merge-config` from the shared `config.shared.yaml` (linked from this
repo) and an optional `config.local.yaml` next to it, for rules that belong to
one Mac only. The local file's lists, such as `window_rules` and `keybindings`,
are appended to the shared ones, and its other keys override them:

```yaml
# ~/.glzr/glazewm/config.local.yaml
window_rules:
  - commands: ["set-floating"]
    match:
      - window_process: { equals: "Some App" }
```

Edit those two files, not `config.yaml`: GlazeWM rebuilds it on startup and on
reload (Left Option+Shift+R), and reloads once more if it changed. Keybindings
in the local file need the same modifiers as the shared file's, as its header
explains. If a file doesn't parse, a notification says so and the last good
config stays. A file that parses but holds a value GlazeWM rejects (a misspelled
command, say) is a different case: GlazeWM shows an error, keeps its loaded
config, and stops rebuilding on reload. To recover, fix the file and run
`~/.local/bin/glazewm-merge-config` by hand. It reloads GlazeWM if it's running.
Otherwise start GlazeWM afterwards.

## glazewm-helper

`install.sh` also sets up a LaunchAgent, `glazewm-helper`. It keeps that
Karabiner rule in step with GlazeWM (restoring it within a minute when Karabiner
restarts), and through sleepwatcher restores the rule and Zebar's bars on wake
(waking from sleep clears one and hides the other). It also restarts Zebar a few
seconds after GlazeWM reports a monitor added or removed, because the bars
vanish then too. It logs what it does, and the sleep and wake events it sees, to
`~/Library/Logs/com.github.gelio.glazewm-helper.log`. `install.sh` only rewrites
and reloads it when it changes, because endpoint security on a managed Mac may
flag that as persistence. If macOS asks, allow it as a background item.
