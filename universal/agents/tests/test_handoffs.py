"""Cross-agent origin and handoff storage migration regressions."""
import importlib.util
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

spec = importlib.util.spec_from_file_location('migration', ROOT / 'migrate-handoff-storage.py')
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


class HandoffTests(unittest.TestCase):
    def test_storage_migration_preserves_old_paths_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            old = home / '.local/claude-handoffs'
            (old / 'repo').mkdir(parents=True)
            (old / 'repo/handoff.md').write_text('handoff chain uses the old path')
            migration.migrate(home)
            migration.migrate(home)
            self.assertTrue(old.is_symlink())
            self.assertEqual((home / '.local/agent-handoffs/repo/handoff.md').read_text(), 'handoff chain uses the old path')
            self.assertEqual((old / 'repo/handoff.md').read_text(), 'handoff chain uses the old path')

    def test_conflicts_abort_before_any_storage_is_moved(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            old = home / '.local/claude-handoffs'
            new = home / '.local/agent-handoffs'
            old.mkdir(parents=True)
            new.mkdir()
            (old / 'a.md').write_text('old')
            (new / 'a.md').write_text('new')
            (old / 'b.md').write_text('must remain')
            with self.assertRaises(RuntimeError):
                migration.migrate(home)
            self.assertFalse((new / 'b.md').exists())
            self.assertEqual((old / 'a.md').read_text(), 'old')

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
