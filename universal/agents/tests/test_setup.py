"""Installation and hook regressions; never mutate the user's home."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import install

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
            for _ in range(2):
                install.merge_settings(home, 'claude')
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

    def test_both_installer_preserves_codex_config_and_personal_hooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.codex').mkdir()
            config = home / '.codex/config.toml'
            config.write_text('model = "personal-model"\n')
            hooks = home / '.codex/hooks.json'
            hooks.write_text(json.dumps({'hooks': {'SessionStart': [{'hooks': [{'type': 'command', 'command': 'echo personal'}]}]}}))
            for _ in range(2):
                subprocess.run(['python3', str(ROOT / 'install.py'), '--agent', 'both', '--target-home', tmp], check=True, capture_output=True)
                result = json.loads(hooks.read_text())
                commands = [h['command'] for m in result['hooks']['SessionStart'] for h in m['hooks']]
                self.assertIn('echo personal', commands)
                self.assertEqual(len(commands), len(set(commands)))
                self.assertEqual(config.read_text(), 'model = "personal-model"\n')
                # Test the installed entry point, not only its repository source.
                result = subprocess.run(['python3', str(home / '.claude/hooks/block-risky-commands.py')], input=json.dumps({'tool_name': 'Bash', 'tool_input': {'command': 'git push'}}), text=True, capture_output=True, check=True)
                self.assertEqual(json.loads(result.stdout)['decision'], 'block')
            self.assertEqual(len(list((home / '.codex').glob('hooks.json.backup-*'))), 1)

class InstallerSafetyTests(unittest.TestCase):
    def test_unmanaged_skill_conflict_preserves_settings_and_handoffs(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            conflict = home / '.agents/skills/commit-conventions/SKILL.md'
            conflict.parent.mkdir(parents=True)
            conflict.write_text('personal skill')
            settings = home / '.claude/settings.json'
            settings.parent.mkdir()
            settings.write_text('{"keep": true}')
            legacy = home / '.local/claude-handoffs/a.md'
            legacy.parent.mkdir(parents=True)
            legacy.write_text('keep handoff')
            result = subprocess.run(['python3', str(ROOT / 'install.py'), '--agent', 'both', '--target-home', tmp], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(settings.read_text(), '{"keep": true}')
            self.assertEqual(legacy.read_text(), 'keep handoff')
            self.assertEqual(conflict.read_text(), 'personal skill')

    def test_existing_python_caches_do_not_conflict_with_installation(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / '.claude/__pycache__/notify_utils.cpython-314.pyc'
            cache.parent.mkdir(parents=True)
            cache.write_bytes(b'personal cache')
            subprocess.run(['python3', str(ROOT / 'install.py'), '--agent', 'both', '--target-home', tmp], check=True, capture_output=True)
            self.assertEqual(cache.read_bytes(), b'personal cache')


if __name__ == '__main__':
    unittest.main()
