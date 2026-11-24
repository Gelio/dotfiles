# Windows (WSL)

Everything here runs from WSL. The universal tools come from
`universal/bootstrap.sh`, as on the other systems.

## Windows-side config

Windows apps can't follow symlinks into WSL, so `config.sh` copies their config
files between `config/` and `%USERPROFILE%`:

```bash
cd windows
./config.sh list           # the files it syncs
./config.sh push glzr      # repo → Windows, for entries matching "glzr"
./config.sh pull keyboard  # Windows → repo, after changing settings in the app
```

Without a filter, `push` and `pull` sync every entry. A directory sync that
would delete files at the destination stops unless you pass `-f`.

It covers GlazeWM, Zebar with the aurora bar theme, PowerToys Keyboard Manager,
and Windows Terminal.

```bash
./glazewm.sh    # installs GlazeWM with winget, pushes its and Zebar's config
./powertoys.sh  # installs PowerToys with winget, pushes Keyboard Manager's config
```

## WSL scripts

```bash
./stow.sh  # links stowed-wsl/ into ~
```

- `git`: runs `git.exe` inside `/mnt/c` and `/mnt/d`, where WSL's git is slow.
- `glazewm-gather-workspaces`: puts GlazeWM's workspaces back on the right
  monitors after Windows drops the external ones during sleep or lock. GlazeWM
  runs it from Alt+Shift+G.
