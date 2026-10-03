"""Installation and hook regressions; never mutate the user's home."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SetupTests(unittest.TestCase):
    def test_settings_merge_is_additive_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.claude').mkdir()
            path = home / '.claude/settings.json'
            existing = {'custom': {'keep': True}, 'enabledPlugins': {'personal@test': True},
                        'hooks': {'SessionStart': [{'matcher': '', 'hooks': [
                            {'type': 'command', 'command': 'echo personal'}]}]}}
            path.write_text(json.dumps(existing))
            env = {**os.environ, 'HOME': tmp}
            for _ in range(2):
                subprocess.run(['node', '--experimental-strip-types', str(ROOT / 'setup-settings.ts')], env=env, check=True, capture_output=True)
                result = json.loads(path.read_text())
                self.assertTrue(result['custom']['keep'])
                self.assertTrue(result['enabledPlugins']['personal@test'])
                commands = [h['command'] for m in result['hooks']['SessionStart'] for h in m['hooks']]
                self.assertEqual(len(commands), len(set(commands)))
                if _ == 0:
                    first = result
                else:
                    self.assertEqual(first, result)

    def hook(self, name, command, **extra):
        payload = {'tool_name': 'Bash', 'tool_input': {'command': command}, **extra}
        result = subprocess.run(['python3', str(ROOT / 'stowed/.claude/hooks' / name)], input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(result.stdout) if result.stdout else None

    def test_claude_command_policy(self):
        for command in ['git push', 'gh pr merge 123', 'rm -rf scratch']:
            self.assertEqual(self.hook('block-risky-commands.py', command)['decision'], 'block')
        self.assertIsNone(self.hook('block-risky-commands.py', 'git status'))
        self.assertEqual(self.hook('block-risky-commands.py', 'npx playwright test')['decision'], 'block')

    def test_claude_commit_policy(self):
        self.assertEqual(self.hook('validate-commit.py', 'git commit -m hello')['decision'], 'block')
        self.assertIsNone(self.hook('validate-commit.py', 'git commit --fixup=abc123'))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'message'
            path.write_text('refactor: share agent setup\n\nReason.\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>\n')
            self.assertIsNone(self.hook('validate-commit.py', 'git commit -F message', cwd=tmp))
            path.write_text('refactor: share agent setup\n')
            self.assertEqual(self.hook('validate-commit.py', 'git commit -F message', cwd=tmp)['decision'], 'block')

if __name__ == '__main__':
    unittest.main()
