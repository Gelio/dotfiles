#!/usr/bin/env python3
"""Codex hook transport for the shared command and commit policies."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.agents/lib'))
from agent_setup.commands import check_command
from agent_setup.commits import check_commit
from agent_setup.fixups import check_fixup


def main():
    data = json.load(sys.stdin)
    if data.get('tool_name') != 'Bash':
        return
    command = data.get('tool_input', {}).get('command', '')
    cwd = data.get('cwd', '')
    event = data.get('hook_event_name', '')
    if event == 'PreToolUse':
        reason = check_command(command) or check_commit(command, cwd, 'codex')
        if reason:
            print(json.dumps({'hookSpecificOutput': {
                'hookEventName': event, 'permissionDecision': 'deny',
                'permissionDecisionReason': reason}}))
    elif event == 'PostToolUse':
        warning = check_fixup(command, cwd)
        if warning:
            print(json.dumps({'hookSpecificOutput': {
                'hookEventName': event, 'additionalContext': warning}}))


if __name__ == '__main__':
    main()
