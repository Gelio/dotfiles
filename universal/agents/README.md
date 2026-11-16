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
`review-settings.py`, edit the partial, or delete the value from the live file;
`MISE_MERGE_ALLOW_LOSS=1` applies anyway. **Removing a key from a partial does
not remove it from the live settings**; delete it there by hand. `mise dot diff`
previews the changes. Restart the agents afterwards; Codex asks you to trust new
hooks.

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

## Settings review

```bash
python3 review-settings.py
```

Walks `~/.claude/settings.json` for entries missing from `settings-partial.json`
and asks whether to adopt or permanently ignore each
(`.settings-review-ignore.json`).
