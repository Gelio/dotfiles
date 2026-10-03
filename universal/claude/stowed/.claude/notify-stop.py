#!/usr/bin/env python3
"""Claude Stop notification adapter."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".agents/lib"))
from agent_setup.notifications import handle_event

if __name__ == "__main__":
    handle_event(json.load(sys.stdin), "Stop")
