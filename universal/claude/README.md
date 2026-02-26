# Claude Code notification hooks

macOS notification hooks for Claude Code using `terminal-notifier`.

- Notifies when Claude needs permission to use a tool (with tool details)
- Notifies when Claude is ready for input
- Skips notifications when the terminal is focused (tmux-aware)
- Auto-dismisses notifications after a few seconds

## Prerequisites

- `terminal-notifier` (`brew install terminal-notifier`)
- Python 3
- Node.js 24+

## Install

```bash
./stow.sh
```

This symlinks the hook scripts into `~/.claude/` and merges the hook
configuration into `~/.claude/settings.json`.
