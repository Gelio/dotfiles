"""Compatibility import for existing Claude notification hooks."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".agents/lib"))
from agent_setup.notifications import *  # noqa: F403
