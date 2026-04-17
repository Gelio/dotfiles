# Claude Code dotfiles

Hooks, notification scripts, and skills for Claude Code.

## What's included

### Settings (`settings-partial.json`)

Portable subset of `~/.claude/settings.json` — hooks, sandbox,
`statusLine`, enabled plugins, permission allowlist, and preferences
(`model`, `alwaysThinkingEnabled`). Merged into the live settings file
by `setup-settings.ts`. Machine-specific entries (AWS/Bedrock env,
`awsAuthRefresh`, personal paths, work-only plugins) stay out of
dotfiles.

### Hooks (`stowed/.claude/hooks/`)

- **validate-commit.py** — enforces commit message conventions (requires
  `-F`, validates format, Co-Authored-By trailer)
- **block-risky-commands.py** — blocks destructive commands (`git push`,
  `reset --hard`, `rm -rf`, `gh pr merge`, etc.)
- **verify-fixup-scope.py** — advisory warning when a fixup commit touches
  files not changed by its target commit

### Notification scripts (`stowed/.claude/`)

- **notify-permission.py** — macOS notification when Claude needs tool permission
- **notify-stop.py** — notification when Claude is ready for input
- **notify-dismiss-permission.py** — dismisses permission notifications
- Skips notifications when the terminal is focused (tmux-aware)

### Skills (`skills/`)

- **commit-conventions** — universal commit authoring rules
- **pr-conventions** — PR description style guide
- **todos** — orchestrate work through a todos.md task list
- **verify-branch-commits** — verify every branch commit passes checks

## Prerequisites

- `terminal-notifier` (`brew install terminal-notifier`)
- Python 3
- Node.js 24+

## Install

### Hooks and notification scripts

```bash
./stow.sh
```

This symlinks scripts into `~/.claude/` and merges
`settings-partial.json` into `~/.claude/settings.json`. The merge is
additive: existing keys, hooks, and permission entries are preserved;
only values also present in the partial are touched. Re-running is
safe.

### Skills

Install all skills globally:

```bash
npx skills add ./skills --global --all
```

Or pick specific ones:

```bash
npx skills add ./skills --global --skill commit-conventions
npx skills add ./skills --global --skill pr-conventions
npx skills add ./skills --global --skill verify-branch-commits
npx skills add ./skills --global --skill todos
```

## Promoting new settings into the partial

When you change something in `~/.claude/settings.json` on a machine and
want it in dotfiles, run:

```bash
node --experimental-strip-types review-settings.ts
```

The script walks the live settings, finds anything not already covered
by `settings-partial.json`, prints each candidate, and prompts:

- **`a`** — adopt into `settings-partial.json`
- **`s`** — skip this run (ask again next time)
- **`i`** — add to `.settings-review-ignore.json` (never ask again)
- **`q`** — quit and save what's been chosen so far

Use `i` for machine-specific entries (AWS env, personal paths, etc.) —
the ignore list is checked in so the same decisions apply on every
machine.
