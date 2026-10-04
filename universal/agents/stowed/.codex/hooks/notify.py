#!/usr/bin/env python3
"""Codex notification adapter; share the backend and isolate notification IDs."""
import json
import os
import sys
from pathlib import Path

os.environ['AGENT_SETUP_AGENT'] = 'codex'
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.agents/lib'))
from agent_setup.notifications import handle_event

if __name__ == '__main__':
    data = json.load(sys.stdin)
    handle_event(data, data.get('hook_event_name', ''))
