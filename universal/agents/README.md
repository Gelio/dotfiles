# Coding agent dotfiles

Skills, hook policy, desktop notifications, and session handoffs shared by
Claude Code and Codex.

## Install

Requires Python 3 and GNU Stow (`jq` for the Claude handoff hook).

```bash
python3 install.py                     # stow shared resources into ~
python3 install.py --dry-run
```

The installer stows `stowed/` into `~`, refusing unmanaged conflicts.

The settings are mise merge entries in `mise/config/config.ai.toml`, applied
by `bootstrap.sh` when the `ai` group is enabled, or by `mise dot apply`. They
merge `settings-partial.json` into `~/.claude/settings.json`,
`codex-hooks-partial.json` into `~/.codex/hooks.json`, and
`codex-config-partial.toml` into `~/.codex/config.toml`. mise owns only the keys in a partial, so keys the agents
write themselves stay. A partial's arrays (permissions, sandbox paths, hooks)
and scalars replace the live ones, and `mise/merge-guard.py` stops the apply
when that would discard a live value, listing each. Adopt Claude settings with
`review-settings.py`, edit the partial, or delete the value from the live file;
`MISE_MERGE_ALLOW_LOSS=1` applies anyway. **Removing a key from a partial does
not remove it from the live settings**; delete it there by hand. `mise dot diff`
previews the changes. Restart the agents afterwards; Codex asks you to trust new
hooks.

## Layout

| Source | Installed as |
| --- | --- |
| `stowed/.agents/skills/<name>/` | `~/.agents/skills/<name>/` (Codex reads this directly) |
| `stowed/.claude/skills/<name>` | `~/.claude/skills/<name>`, a link to the shared skill |
| `stowed/.agents/lib/agent_setup/` | Shared hook policy and notifications |
| `stowed/.claude/`, `stowed/.codex/` | Per-agent hook adapters |
| `stowed/.agents/.skill-lock.json` | Third-party skill selections (`npx skills`) |

Edit authored skills under `stowed/.agents/skills/`.

## Hooks

Both agents block `git push`, destructive `gh` commands, and `rm -rf`; require
`git commit -F <file>`; and warn when a fixup touches files its target didn't.
Claude additionally requires the sandbox to be disabled for Playwright, auto-allows
handoff file access, and has a status line. Notifications use `terminal-notifier`
on macOS and Windows toasts on WSL, and are skipped while the session is focused.

## Handoffs

Handoffs live in `~/.local/agent-handoffs/<repo-key>/`. The SessionStart hooks
record each session's launch repository so a later `cd` doesn't redirect a
handoff. Codex gets that path in its session context and passes it explicitly;
run `codex-agent` (or `codex --add-dir ~/.local/agent-handoffs`) so it can write
there.

## Third-party skills

```bash
python3 bootstrap-skills.py            # print restore commands from the lockfile
python3 bootstrap-skills.py --apply
npx skills update -g
```

Restoring fetches current upstream content; lockfile hashes are not pins.

## Settings review

```bash
python3 review-settings.py
```

Walks `~/.claude/settings.json` for entries missing from `settings-partial.json`
and asks whether to adopt or permanently ignore each
(`.settings-review-ignore.json`).

## Tests

```bash
python3 -m unittest discover -s tests
python3 -m unittest discover -s stowed/.agents/skills/session-handoff/evals -p 'test_*.py'
```

`skill-evals/` benchmarks skill bodies through Claude; see its README.
