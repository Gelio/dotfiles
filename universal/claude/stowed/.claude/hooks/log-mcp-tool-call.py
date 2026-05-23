#!/usr/bin/env python3
"""PreToolUse hook: log MCP tool calls to ~/.cache/claude-mcp-calls/ for inspection."""
import json
import re
import sys
import time
from pathlib import Path

OUT_DIR = Path.home() / ".cache" / "claude-mcp-calls"


def unwrap_json_strings(value):
    """Recursively replace string values that contain JSON objects/arrays with the parsed form."""
    if isinstance(value, dict):
        return {k: unwrap_json_strings(v) for k, v in value.items()}
    if isinstance(value, list):
        return [unwrap_json_strings(v) for v in value]
    if isinstance(value, str):
        stripped = value.lstrip()
        if stripped.startswith(("{", "[")):
            try:
                parsed = json.loads(stripped)
            except (ValueError, TypeError):
                return value
            if isinstance(parsed, (dict, list)):
                return unwrap_json_strings(parsed)
        return value
    return value


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool = data.get("tool_name", "unknown")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    now = time.time()
    ts = time.strftime("%Y%m%d-%H%M%S", time.localtime(now))
    ms = f"{int((now % 1) * 1000):03d}"
    safe_tool = re.sub(r"[^A-Za-z0-9_-]", "_", tool)
    path = OUT_DIR / f"{ts}-{ms}-{safe_tool}.json"

    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)) + f".{ms}",
        "tool_name": tool,
        "session_id": data.get("session_id"),
        "cwd": data.get("cwd"),
        "tool_input": unwrap_json_strings(data.get("tool_input")),
    }
    path.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
