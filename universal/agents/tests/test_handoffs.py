"""Cross-agent session origins and shared handoff storage."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'stowed/.agents/skills/session-handoff/scripts'))
from _handoff_paths import capture_origin, resolve_project_root



class HandoffTests(unittest.TestCase):
    def test_namespaced_session_origins_survive_cwd_change_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'HOME': tmp}, clear=True):
            home = Path(tmp)
            first = home / 'first'
            second = home / 'second'
            for repo in [first, second]:
                repo.mkdir()
                subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            capture_origin({'session_id': 'same-id', 'cwd': str(first)}, 'claude')
            self.assertEqual(capture_origin({'session_id': 'same-id', 'cwd': str(second)}, 'codex'), str(second))
            # A resumed session keeps its first origin.
            self.assertEqual(capture_origin({'session_id': 'same-id', 'cwd': str(second)}, 'claude'), str(first))
            with patch.dict(os.environ, {'CLAUDE_CODE_SESSION_ID': 'same-id'}):
                self.assertEqual(resolve_project_root(), str(first))
            self.assertEqual(resolve_project_root(str(second)), str(second))

    def test_claude_and_codex_create_handoffs_in_the_same_repo_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            repo = home / 'repo'
            repo.mkdir()
            env = {**os.environ, 'HOME': tmp}
            for agent in ['claude', 'codex']:
                payload = {'session_id': f'{agent}-session', 'cwd': str(repo), 'hook_event_name': 'SessionStart'}
                adapter = ROOT / ('stowed/.claude/hooks/capture-handoff-origin.py' if agent == 'claude' else 'stowed/.codex/hooks/session-start.py')
                result = subprocess.run(['python3', str(adapter)], input=json.dumps(payload), text=True, capture_output=True, env=env, check=True)
                if agent == 'codex':
                    self.assertIn(str(repo), json.loads(result.stdout)['hookSpecificOutput']['additionalContext'])
                subprocess.run(['python3', str(ROOT / 'stowed/.agents/skills/session-handoff/scripts/create_handoff.py'), agent, '--project-dir', str(repo)], cwd=tmp, env=env, check=True, capture_output=True)
            files = list((home / '.local/agent-handoffs').glob('*/*.md'))
            self.assertEqual(len(files), 2)
            self.assertEqual(files[0].parent, files[1].parent)
            for path in files:
                self.assertIn(str(repo), path.read_text())

if __name__ == '__main__':
    unittest.main()
