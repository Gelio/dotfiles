"""Installation and hook regressions; never mutate the user's home."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SetupTests(unittest.TestCase):
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
        self.assertEqual(self.hook('validate-commit.py', 'git commit')['decision'], 'block')
        self.assertIsNone(self.hook('validate-commit.py', 'git commit --fixup=abc123'))
        # Attribution is left to the agent; any -F message passes.
        self.assertIsNone(self.hook('validate-commit.py', 'git commit -F message'))

class SkillLayoutTests(unittest.TestCase):
    def test_stow_links_shared_skills_without_owning_third_party(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            for directory in ['.agents/skills', '.claude/skills', '.claude/hooks']:
                (home / directory).mkdir(parents=True, exist_ok=True)
            third_party = home / '.agents/skills/external/SKILL.md'
            third_party.parent.mkdir()
            third_party.write_text('external')
            for _ in range(2):
                subprocess.run(['stow', '-R', '-d', str(ROOT), '-t', tmp, 'stowed'], check=True, capture_output=True)
                for source in (ROOT / 'stowed/.agents/skills').iterdir():
                    self.assertEqual((home / '.agents/skills' / source.name).resolve(), source.resolve())
                    self.assertEqual((home / '.claude/skills' / source.name).resolve(), source.resolve())
                self.assertEqual(third_party.read_text(), 'external')

class CodexTests(unittest.TestCase):
    def codex_hook(self, command, cwd=''):
        payload = {'hook_event_name': 'PreToolUse', 'tool_name': 'Bash',
                   'tool_input': {'command': command}, 'cwd': cwd}
        result = subprocess.run(['python3', str(ROOT / 'stowed/.codex/hooks/agent-policy.py')], input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(result.stdout) if result.stdout else None

    def test_codex_shares_command_policy_without_claude_sandbox_flag(self):
        self.assertEqual(self.codex_hook('git push')['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.codex_hook('git commit -m hello')['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertIsNone(self.codex_hook('git commit -F message'))
        self.assertIsNone(self.codex_hook('npx playwright test'))

    def test_installer_links_hook_entry_points(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            for _ in range(2):
                subprocess.run(['python3', str(ROOT / 'install.py'), '--target-home', tmp], check=True, capture_output=True)
                # Test the installed entry point, not only its repository source.
                result = subprocess.run(['python3', str(home / '.claude/hooks/block-risky-commands.py')], input=json.dumps({'tool_name': 'Bash', 'tool_input': {'command': 'git push'}}), text=True, capture_output=True, check=True)
                self.assertEqual(json.loads(result.stdout)['decision'], 'block')

class InstallerSafetyTests(unittest.TestCase):
    def test_unmanaged_skill_conflict_aborts_without_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            conflict = home / '.agents/skills/commit-conventions/SKILL.md'
            conflict.parent.mkdir(parents=True)
            conflict.write_text('personal skill')
            result = subprocess.run(['python3', str(ROOT / 'install.py'), '--target-home', tmp], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(conflict.read_text(), 'personal skill')
            self.assertFalse((home / '.claude/hooks/block-risky-commands.py').exists())

    def test_existing_python_caches_do_not_conflict_with_installation(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / '.claude/__pycache__/notify_utils.cpython-314.pyc'
            cache.parent.mkdir(parents=True)
            cache.write_bytes(b'personal cache')
            subprocess.run(['python3', str(ROOT / 'install.py'), '--target-home', tmp], check=True, capture_output=True)
            self.assertEqual(cache.read_bytes(), b'personal cache')


if __name__ == '__main__':
    unittest.main()
