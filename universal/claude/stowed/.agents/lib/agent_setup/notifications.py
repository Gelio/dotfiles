"""Shared utilities for coding-agent notification hooks.

Supported platforms:
  - macOS: terminal-notifier + osascript focus detection.
  - WSL:   native Windows toasts via powershell.exe (no extra modules needed).
  - Anything else: notifications are silently skipped.
"""

import base64
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from xml.sax.saxutils import escape

HOME = os.path.expanduser("~")

# Marks a permission notification that may still be on screen, so the
# PostToolUse/Stop hooks only spawn a removal when there is something to remove
# (spawning powershell.exe on every tool call would be far too slow).
AGENT = os.environ.get("AGENT_SETUP_AGENT", "claude")
AGENT_LABEL = "Codex" if AGENT == "codex" else "Claude Code"

STATE_DIR = Path(tempfile.gettempdir()) / f"{AGENT}-notify"


def _is_wsl() -> bool:
    if not sys.platform.startswith("linux"):
        return False
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


if sys.platform == "darwin" and shutil.which("terminal-notifier"):
    PLATFORM = "macos"
elif _is_wsl() and shutil.which("powershell.exe"):
    PLATFORM = "wsl"
else:
    PLATFORM = None


def shorten_path(path: str) -> str:
    """Shorten a path for display in notifications.

    Replaces HOME prefix with ~ and collapses middle segments for long paths.
    """
    if not path:
        return path
    if path.startswith(HOME):
        path = "~" + path[len(HOME):]
    # If still long, keep first and last 2 segments with … in the middle
    parts = path.split("/")
    if len(parts) > 5:
        path = "/".join(parts[:2]) + "/…/" + "/".join(parts[-2:])
    return path


def _tmux_context() -> tuple[str, str] | None:
    """Return (window, pane title) of the tmux pane running this session.

    Claude Code sets the pane title to a summary of the conversation, prefixed
    with a status glyph (✳ or a spinner), which is stripped here. The pane title
    is empty when it is still tmux's default (the hostname).
    """
    pane = os.environ.get("TMUX_PANE")
    if not pane:
        return None
    result = subprocess.run(
        ["tmux", "display-message", "-p", "-t", pane,
         "#{window_index}:#{window_name}\t#{pane_title}\t#{host}\t#{host_short}"],
        capture_output=True,
        text=True,
    )
    fields = result.stdout.rstrip("\n").split("\t")
    if result.returncode != 0 or len(fields) != 4:
        return None
    window, pane_title, host, host_short = fields
    if pane_title in (host, host_short):
        pane_title = ""
    return window, re.sub(r"^\W+", "", pane_title).strip()


def describe_session(cwd: str) -> tuple[str, str]:
    """Build a notification (title, subtitle) identifying this session.

    Title is the conversation summary from the tmux pane title, falling back to
    the project name. Subtitle names the tmux window and the shortened cwd.
    """
    project = cwd.split("/")[-1] if cwd else "unknown"
    tmux = _tmux_context()
    window, pane_title = tmux if tmux else ("", "")
    title = pane_title or f"{AGENT_LABEL} — {project}"
    subtitle = " · ".join(part for part in (window, shorten_path(cwd)) if part)
    return title, subtitle


def notification_group(kind: str, cwd: str) -> str:
    """Group id for a session's notifications of `kind` ("permission"/"stop").

    Keyed by tmux pane so sessions sharing a cwd don't replace or dismiss each
    other's notifications; falls back to cwd outside tmux.
    """
    return f"{AGENT}-{kind}-{os.environ.get('TMUX_PANE') or cwd}"


def _pending_marker(group: str) -> Path:
    return STATE_DIR / hashlib.sha1(group.encode()).hexdigest()


def notify(title: str, subtitle: str, message: str, *, kind: str, group: str,
           dismiss_after: int):
    """Show a notification unless the user is already looking at this session.

    `kind` is "permission" or "stop"; it picks the sound. Notifications in the
    same `group` replace each other and can be removed with `remove(group)`.
    """
    if PLATFORM == "macos":
        if _is_session_visible_macos():
            return
        sound = "Funk" if kind == "permission" else "Glass"
        subprocess.run([
            "terminal-notifier",
            "-title", title,
            "-subtitle", subtitle,
            "-message", message,
            "-sound", sound,
            "-group", group,
        ])
        _auto_dismiss_macos(group, dismiss_after)
    elif PLATFORM == "wsl":
        # Mirror macOS: outside tmux always notify; inside tmux, an inactive
        # pane means the session isn't visible, so skip the Windows focus check.
        check_focus = bool(os.environ.get("TMUX_PANE")) and _is_tmux_pane_active()
        _toast_wsl(title, subtitle, message, kind=kind, group=group,
                   dismiss_after=dismiss_after, check_focus=check_focus)
    else:
        return
    STATE_DIR.mkdir(exist_ok=True)
    _pending_marker(group).touch()


def remove(group: str):
    """Remove a notification shown by `notify`, if one may still be visible."""
    marker = _pending_marker(group)
    if not marker.exists():
        return
    marker.unlink(missing_ok=True)
    if PLATFORM == "macos":
        subprocess.run(["terminal-notifier", "-remove", group])
    elif PLATFORM == "wsl":
        tag, toast_group = _toast_ids(group)
        _run_powershell_detached(
            f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null\n"
            f"[Windows.UI.Notifications.ToastNotificationManager]::History.Remove("
            f"{_ps_str(tag)}, {_ps_str(toast_group)}, {_ps_str(_WSL_APP_ID)})\n"
        )


# --- macOS -------------------------------------------------------------------

def _auto_dismiss_macos(group: str, delay_seconds: int):
    """Remove a terminal-notifier group after a delay, unless a newer notification replaced it."""
    token = str(time.time())
    safe_group = group.replace("/", "_")
    token_file = f"/tmp/{AGENT}-notify-{safe_group}.token"
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


def _is_terminal_focused_macos():
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


def _is_session_visible_macos():
    """Check if the user is currently looking at this Claude Code session.

    Returns True if the terminal is focused AND the tmux pane (if any) is active.
    """
    if not _is_terminal_focused_macos():
        return False

    # If running inside tmux, also check that this pane is the active one
    if os.environ.get("TMUX_PANE"):
        return _is_tmux_pane_active()

    return False


# --- WSL (Windows toasts) ----------------------------------------------------

# AppUserModelID of Windows PowerShell; registered on every Windows install, so
# toasts work without creating a Start menu shortcut for a custom app id.
_WSL_APP_ID = r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"

# Windows process names of terminal emulators (foreground window owner).
WINDOWS_TERMINAL_PROCESSES = {
    "WindowsTerminal",
    "wezterm-gui",
    "alacritty",
    "kitty",
    "Hyper",
    "Warp",
    "ghostty",
}

_WSL_SOUNDS = {
    "permission": "ms-winsoundevent:Notification.Reminder",
    "stop": "ms-winsoundevent:Notification.Default",
}


def _ps_str(value: str) -> str:
    """Quote a trusted constant as a PowerShell single-quoted string literal."""
    return "'" + value.replace("'", "''") + "'"


def _toast_ids(group: str) -> tuple[str, str]:
    """Map a group name to a toast (tag, group); Windows caps both at 64 chars."""
    return hashlib.sha1(group.encode()).hexdigest()[:32], f"{AGENT}-code"


def _run_powershell_detached(script: str):
    """Run a PowerShell script in the background; powershell.exe takes ~1s to start."""
    encoded = base64.b64encode(script.encode("utf-16-le")).decode()
    subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-NonInteractive",
         "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _toast_wsl(title: str, subtitle: str, message: str, *, kind: str,
               group: str, dismiss_after: int, check_focus: bool):
    tag, toast_group = _toast_ids(group)
    xml = (
        '<toast><visual><binding template="ToastGeneric">'
        f"<text>{escape(title)}</text>"
        f"<text>{escape(message)}</text>"
        f'<text placement="attribution">{escape(subtitle)}</text>'
        "</binding></visual>"
        f'<audio src="{_WSL_SOUNDS.get(kind, _WSL_SOUNDS["stop"])}"/>'
        "</toast>"
    )
    focus_check = ""
    if check_focus:
        terminals = ", ".join(_ps_str(p) for p in sorted(WINDOWS_TERMINAL_PROCESSES))
        focus_check = (
            "Add-Type -Namespace ClaudeNotify -Name User32 -MemberDefinition '"
            '[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); '
            '[DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);'
            "'\n"
            "$fgPid = [uint32]0\n"
            "[void][ClaudeNotify.User32]::GetWindowThreadProcessId([ClaudeNotify.User32]::GetForegroundWindow(), [ref]$fgPid)\n"
            "$fgName = (Get-Process -Id $fgPid -ErrorAction SilentlyContinue).ProcessName\n"
            f"if (@({terminals}) -contains $fgName) {{ exit }}\n"
        )
    _run_powershell_detached(
        focus_check
        + "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null\n"
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null\n"
        "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument\n"
        # Base64 keeps untrusted text (commands, paths) out of the PowerShell
        # source; PowerShell also treats curly quotes as string delimiters.
        "$xml.LoadXml([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("
        f"'{base64.b64encode(xml.encode()).decode()}')))\n"
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)\n"
        f"$toast.Tag = {_ps_str(tag)}\n"
        f"$toast.Group = {_ps_str(toast_group)}\n"
        f"$toast.ExpirationTime = [DateTimeOffset]::Now.AddSeconds({int(dismiss_after)})\n"
        f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier({_ps_str(_WSL_APP_ID)}).Show($toast)\n"
    )


def handle_event(data: dict, event: str) -> None:
    """Present the same notification behavior through either agent's hooks."""
    cwd = data.get('cwd', '')
    if event == 'PostToolUse':
        remove(notification_group('permission', cwd))
        return
    title, subtitle = describe_session(cwd)
    if event == 'Stop':
        remove(notification_group('permission', cwd))
        notify(title, subtitle, 'Ready for input', kind='stop',
               group=notification_group('stop', cwd), dismiss_after=5)
    elif event == 'PermissionRequest':
        tool = data.get('tool_name', 'unknown')
        args = data.get('tool_input', {})
        detail = ''
        if tool in {'Bash', 'apply_patch'}:
            detail = shorten_path(args.get('command', '')[:100])
        elif tool in {'Edit', 'Write', 'Read'}:
            path = args.get('file_path', '')
            detail = path[len(cwd) + 1:] if cwd and path.startswith(cwd + '/') else shorten_path(path)
        message = f'Permission needed: {tool}' + (f' — {detail}' if detail else '')
        notify(title, subtitle, message, kind='permission',
               group=notification_group('permission', cwd), dismiss_after=10)
