"""Hook regressions; never mutate the user's home."""
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SetupTests(unittest.TestCase):
    def hook(self, name, command, **extra):
        payload = {'tool_name': 'Bash', 'tool_input': {'command': command}, **extra}
        result = subprocess.run(['python3', str(ROOT / 'home/.claude/hooks' / name)], input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(result.stdout) if result.stdout else None

    def test_claude_command_policy(self):
        for command in ['git push', 'gh pr merge 123', 'rm -rf scratch']:
            self.assertEqual(self.hook('block-risky-commands.py', command)['decision'], 'block')
        self.assertIsNone(self.hook('block-risky-commands.py', 'git status'))
        self.assertEqual(self.hook('block-risky-commands.py', 'npx playwright test')['decision'], 'block')

    def test_claude_commit_policy(self):
        self.assertEqual(self.hook('validate-commit.py', 'git commit -m hello')['decision'], 'block')
        self.assertEqual(self.hook('validate-commit.py', 'git commit')['decision'], 'block')
        self.assertIsNone(self.hook('validate-commit.py', 'git commit --fixup=abc123'))
        # Attribution is left to the agent; any -F message passes.
        self.assertIsNone(self.hook('validate-commit.py', 'git commit -F message'))

class CodexTests(unittest.TestCase):
    def codex_hook(self, command, cwd=''):
        payload = {'hook_event_name': 'PreToolUse', 'tool_name': 'Bash',
                   'tool_input': {'command': command}, 'cwd': cwd}
        result = subprocess.run(['python3', str(ROOT / 'home/.codex/hooks/agent-policy.py')], input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(result.stdout) if result.stdout else None

    def test_codex_shares_command_policy_without_claude_sandbox_flag(self):
        self.assertEqual(self.codex_hook('git push')['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.codex_hook('git commit -m hello')['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertIsNone(self.codex_hook('git commit -F message'))
        self.assertIsNone(self.codex_hook('npx playwright test'))

if __name__ == '__main__':
    unittest.main()
