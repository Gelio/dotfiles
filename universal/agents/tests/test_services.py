"""Verify shared services with observable results, without desktop side effects."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'home/.agents/lib'))
from agent_setup import notifications
from agent_setup.fixups import check_fixup


class ServicesTests(unittest.TestCase):
    def test_notification_lifecycle_preserves_permission_dismissal(self):
        with patch.object(notifications, 'notify') as notify, patch.object(notifications, 'remove') as remove, patch.object(notifications, '_tmux_context', return_value=None):
            data = {'cwd': '/tmp/project', 'tool_name': 'Bash', 'tool_input': {'command': 'git push'}}
            notifications.handle_event(data, 'PermissionRequest')
            self.assertEqual(notify.call_args.args[2], 'Permission needed: Bash — git push')
            notifications.handle_event(data, 'PostToolUse')
            self.assertEqual(remove.call_args.args[0], notifications.notification_group('permission', '/tmp/project'))
            notifications.handle_event(data, 'Stop')
            self.assertEqual(notify.call_args.args[2], 'Ready for input')
            self.assertEqual(remove.call_count, 2)

    def test_fixup_scope_uses_tool_cwd_and_remains_advisory(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            def git(*args):
                return subprocess.run(['git', '-C', tmp, *args], check=True, capture_output=True, text=True).stdout.strip()
            git('init', '-q')
            git('config', 'user.name', 'Test')
            git('config', 'user.email', 'test@example.com')
            git('config', 'commit.gpgsign', 'false')
            git('config', 'core.hooksPath', '/dev/null')
            (repo / 'base').write_text('base')
            git('add', 'base')
            git('commit', '-qm', 'base')
            (repo / 'target').write_text('target')
            git('add', 'target')
            git('commit', '-qm', 'target')
            target = git('rev-parse', 'HEAD')
            (repo / 'extra').write_text('extra')
            git('add', 'extra')
            git('commit', '-q', f'--fixup={target}')
            command = f'git commit --fixup={target}'
            self.assertIn('Extra files in this fixup: extra', check_fixup(command, tmp))
            for adapter in ['home/.claude/hooks/verify-fixup-scope.py', 'home/.codex/hooks/agent-policy.py']:
                payload = {'hook_event_name': 'PostToolUse', 'tool_name': 'Bash', 'tool_input': {'command': command}, 'cwd': tmp}
                result = subprocess.run(['python3', str(ROOT / adapter)], input=json.dumps(payload), text=True, capture_output=True, check=True)
                data = json.loads(result.stdout)
                self.assertNotIn('decision', data)
                self.assertIn('extra', data['hookSpecificOutput']['additionalContext'])


if __name__ == '__main__':
    unittest.main()
