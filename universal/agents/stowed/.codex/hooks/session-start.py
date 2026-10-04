#!/usr/bin/env python3
"""Capture Codex origin and tell the agent how to pass it to handoff scripts."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.agents/skills/session-handoff/scripts'))
from _handoff_paths import capture_origin


def main():
    Path('/tmp/agent-work').mkdir(parents=True, exist_ok=True)
    data = json.load(sys.stdin)
    origin = capture_origin(data, 'codex')
    if origin:
        context = (f'The launch repository for this session is {json.dumps(origin)}. '
                   'When using session-handoff, pass that path explicitly: '
                   'create_handoff.py --project-dir <launch-repository>, or '
                   'list_handoffs.py <launch-repository>. Preserve it after changing cwd. '
                   'Shared handoffs live in ~/.local/agent-handoffs.')
        print(json.dumps({'hookSpecificOutput': {
            'hookEventName': 'SessionStart', 'additionalContext': context}}))


if __name__ == '__main__':
    main()
