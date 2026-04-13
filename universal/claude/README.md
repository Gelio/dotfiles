# Claude Code dotfiles

Hooks, notification scripts, and skills for Claude Code.

## What's included

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

This symlinks scripts into `~/.claude/` and merges hook configuration
into `~/.claude/settings.json`.

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
