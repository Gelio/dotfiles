"""Shared utilities for Claude Code notification hooks."""

import os
import subprocess
import time


def auto_dismiss(group: str, delay_seconds: int = 5):
    """Remove a terminal-notifier group after a delay, unless a newer notification replaced it."""
    token = str(time.time())
    safe_group = group.replace("/", "_")
    token_file = f"/tmp/claude-notify-{safe_group}.token"
    with open(token_file, "w") as f:
        f.write(token)
    subprocess.Popen(
        [
            "bash", "-c",
            f"sleep {delay_seconds} && "
            f"[ \"$(cat '{token_file}' 2>/dev/null)\" = '{token}' ] && "
            f"terminal-notifier -remove '{group}'"
        ],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

TERMINAL_APPS = {
    "kitty",
    "iTerm2",
    "Terminal",
    "Alacritty",
    "WezTerm",
    "Hyper",
    "Rio",
    "Warp",
    "Ghostty",
}


def _is_terminal_focused():
    """Check if a terminal emulator is the frontmost application."""
    result = subprocess.run(
        [
            "osascript",
            "-e",
            'tell application "System Events" to get name of first application process whose frontmost is true',
        ],
        capture_output=True,
        text=True,
    )
    frontmost = result.stdout.strip()
    return frontmost in TERMINAL_APPS


def _is_tmux_pane_active():
    """Check if the tmux pane running this session is visible and focused."""
    pane = os.environ.get("TMUX_PANE")
    if not pane:
        return False

    result = subprocess.run(
        [
            "tmux",
            "display-message",
            "-p",
            "-t",
            pane,
            "#{pane_active} #{window_active} #{session_attached}",
        ],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() == "1 1 1"


def is_session_visible():
    """Check if the user is currently looking at this Claude Code session.

    Returns True if the terminal is focused AND the tmux pane (if any) is active.
    """
    if not _is_terminal_focused():
        return False

    # If running inside tmux, also check that this pane is the active one
    if os.environ.get("TMUX_PANE"):
        return _is_tmux_pane_active()

    return False
