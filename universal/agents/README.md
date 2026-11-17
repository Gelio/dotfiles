# Coding agent dotfiles

Skills and settings shared by Claude Code and Codex.

## Install

Enable the `ai` group in `mise/config/miserc.toml` and run `bootstrap.sh` (or
`mise dot apply`). Requires Python 3.

The `agents` dotfile group in `mise/config/config.ai.toml` links each file of
`home/` that is in git into `~`. A new file is linked by the next apply after
`git add`.

Merge entries in the same file merge `codex-hooks-partial.json` into
`~/.codex/hooks.json` and `codex-config-partial.toml` into
`~/.codex/config.toml`. mise owns only the keys in a partial, so keys the agents
write themselves stay. A partial's arrays (permissions, sandbox paths, hooks)
and scalars replace the live ones, and `mise/merge-guard.py` stops the apply
when that would discard a live value, listing each. Adopt Claude settings with
`review-settings.py`, edit the partial, keep the value in a
[machine-local overlay](#machine-local-settings), or delete it from the live
file; `MISE_MERGE_ALLOW_LOSS=1` applies anyway. **Removing a key from a partial
does not remove it from the live settings**; delete it there by hand.
`mise dot diff` previews the changes. Restart the agents afterwards; Codex asks
you to trust new hooks.

## Machine-local settings

Entries that belong to one machine only, such as a work proxy in the sandbox's
`allowedDomains`, go in an overlay outside the repo, at the target's path under
`~/.config/dotfiles/local/` (or `$XDG_CONFIG_HOME/dotfiles/local/`):

| Target                    | Overlay                                          |
| ------------------------- | ------------------------------------------------ |
| `~/.claude/settings.json` | `~/.config/dotfiles/local/.claude/settings.json` |
| `~/.codex/hooks.json`     | `~/.config/dotfiles/local/.codex/hooks.json`     |
| `~/.codex/config.toml`    | `~/.config/dotfiles/local/.codex/config.toml`    |

An overlay is in its target's format and holds only the additions:

```json
{
  "sandbox": {
    "network": { "allowedDomains": ["proxy.example.com"] },
    "excludedCommands": ["ps *"]
  }
}
```

Each merge entry's source is a `.tera` template next to its partial. When the
overlay exists, the template runs `mise/merge_local.py`, which combines the two
before mise merges the result into the target: objects merge key by key, arrays
get the overlay's items that the partial lacks appended after the partial's own,
and other overlay values replace the partial's. Without an overlay the template
renders the partial unchanged. `mise dot diff` and `mise dot status` show the
combined result, and `merge-guard.py` and `review-settings.py` count overlay
entries as known. `review-settings.py` can also move a live entry into the
overlay (`[l]ocal`). Deleting an entry from an overlay doesn't delete it from
the live file, as with a partial.

## Layout

| Source                        | Installed as                                                                                                                       |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `home/.agents/skills/<name>/` | `~/.agents/skills/<name>/` (Codex reads this directly)                                                                             |
| `home/.claude/skills/<name>`  | `~/.claude/skills/<name>`, a link to the shared skill                                                                              |
| `vendored-skills.json`        | Upstream repo, folder and pinned commit of each vendored skill                                                                     |
| `personal/`                   | Linked into `~` only with the `personal` group: instructions for a personal Claude subscription, such as reading plan usage limits |

Edit authored skills under `home/.agents/skills/`.

## Vendored skills

Third-party skills are copied into `home/.agents/skills/` and committed, so
installing them needs nothing beyond the mise apply above.
`vendored-skills.json` records where each came from.

```bash
./update-skills.py --latest            # move every pin to upstream's latest commit
./update-skills.py --latest grilling   # just one skill
./update-skills.py                     # re-copy at the pinned commits
```

Review the result with `git diff` before committing: it shows upstream's changes
and any local edits the update overwrote. A new skill needs a manifest entry
(`repo`, `path` of its folder, empty `commit`) and a run with `--latest`; the
script then prints the `.oxfmtrc.jsonc` line that keeps upstream's formatting.
To customize a vendored skill, fork it: drop its manifest entry and keep the
upstream credit in its `metadata.credits`.

### Moving off `npx skills`

On a machine that installed skills with `npx skills`, `~/.agents/skills/<name>/`
holds real folders where mise now links files. Before the next apply, delete
those folders and their `~/.claude/skills/<name>` links for every skill in
`vendored-skills.json` and for the dropped `grill-me`, `grill-with-docs`,
`improve-codebase-architecture`, `setup-matt-pocock-skills`, `teach` and
`retro`.

## Settings review

```bash
python3 review-settings.py
```

Walks `~/.claude/settings.json` for entries missing from `settings-partial.json`
and the machine's overlay, and asks whether to adopt each into the partial, keep
it in the overlay, or permanently ignore it (`.settings-review-ignore.json`).
