# Coding agent dotfiles

Skills, hook policy, desktop notifications, and session handoffs shared by
Claude Code and Codex.

## Install

Requires Python 3 and GNU Stow (`jq` for the Claude handoff hook).

```bash
python3 install.py                     # Claude settings (default)
python3 install.py --agent both        # Claude + Codex
python3 install.py --agent both --dry-run
```

The installer stows `stowed/` into `~` (refusing unmanaged conflicts), then
merges `settings-partial.json` into `~/.claude/settings.json`,
`codex-hooks-partial.json` into `~/.codex/hooks.json`, and
`codex-config-partial.toml` into `~/.codex/config.toml`. The merge is additive
and idempotent: it never removes keys or hooks, and backs up a file before
changing it. In `config.toml` it only adds missing keys, so a key you've set
to a different value stays as is (the installer prints which). **Removing something from a partial does not remove it from the live
settings**; delete it there by hand. Restart the agents afterwards; Codex asks
you to trust new hooks.

## Layout

| Source | Installed as |
| --- | --- |
| `stowed/.agents/skills/<name>/` | `~/.agents/skills/<name>/` (Codex reads this directly) |
| `stowed/.claude/skills/<name>` | `~/.claude/skills/<name>`, a link to the shared skill |
| `stowed/.agents/lib/agent_setup/` | Shared hook policy and notifications |
| `stowed/.claude/`, `stowed/.codex/` | Per-agent hook adapters |
| `stowed/.agents/.skill-lock.json` | Third-party skill selections (`npx skills`) |

Edit authored skills under `stowed/.agents/skills/`. Claude hook paths are
kept stable on purpose: renaming one would leave the old command registered by
the additive merge.

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
