"""Hook regressions; never mutate the user's home."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SetupTests(unittest.TestCase):
    def hook(self, name, command, **extra):
        payload = {'tool_name': 'Bash', 'tool_input': {'command': command}, **extra}
        result = subprocess.run(['python3', str(ROOT / 'home/.claude/hooks' / name)], input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(result.stdout) if result.stdout else None

    def setUp(self):
        # A fake HOME whose user settings enable the sandbox, so results don't
        # depend on the live ~/.claude/settings.json.
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        self.user_settings({'sandbox': {'enabled': True}})

    def user_settings(self, settings):
        path = Path(self.home.name) / '.claude/settings.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(settings))

    def blocked(self, command, cwd, **tool_input):
        payload = {'tool_name': 'Bash', 'cwd': cwd, 'tool_input': {'command': command, **tool_input}}
        result = subprocess.run(['python3', str(ROOT / 'home/.claude/hooks/block-risky-commands.py')], input=json.dumps(payload), text=True, capture_output=True, check=True, env={**os.environ, 'HOME': self.home.name})
        return bool(result.stdout) and json.loads(result.stdout)['decision'] == 'block'

    def git_repo(self, tmp, branch):
        def git(*args):
            subprocess.run(['git', '-C', tmp, *args], check=True, capture_output=True)
        git('init', '-q', '-b', 'main')
        git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '--no-verify', '-q', '--allow-empty', '-m', 'init')
        git('tag', 'v1.0')
        git('remote', 'add', 'origin', f'{tmp}/origin.git')
        git('remote', 'add', 'upstream', f'{tmp}/upstream.git')
        if branch != 'main':
            git('switch', '-q', '-c', branch)

    def test_claude_command_policy(self):
        self.assertTrue(self.blocked('gh pr merge 123', '/tmp'))
        self.assertFalse(self.blocked('gh pr comment 5 --body close', '/tmp'))
        for command in ['GH_REPO=x gh pr merge 1', 'env gh pr merge 1', 'gh repo delete o/r',
                        'gh api -X DELETE repos/o/r/git/refs/heads/main', 'gh api --method=PUT repos/o/r/pulls/1/merge']:
            self.assertTrue(self.blocked(command, '/tmp'), command)
        self.assertFalse(self.blocked('gh api repos/o/r/pulls/1/reviews --method POST --input -', '/tmp'))
        self.assertFalse(self.blocked('git status', '/tmp'))
        self.assertTrue(self.blocked('npx playwright test', '/tmp'))

    def test_git_push_allows_feature_branches_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.git_repo(tmp, 'feature')
            for command in ['git push', 'git push -u origin feature', 'git push origin HEAD', f'git -C {tmp} push origin feature:feature']:
                self.assertFalse(self.blocked(command, tmp), command)
            for command in ['git push origin main', 'git push origin HEAD:master', 'git push --force', 'git push -uf origin feature',
                            'git push --force-with-lease', 'git push origin +feature', 'git push origin :feature', 'git push --delete origin feature',
                            'git push origin v1.0', 'git push --tags', 'git push --all',
                            'git push --repo origin main', 'git push --repo=origin main', 'git push --forc origin feature',
                            'git push --del origin feature', 'git push --mirr', 'git push origin develop', 'git push origin feature:release/1.2',
                            'git -c remote.origin.push=refs/heads/feature:refs/heads/main push origin feature',
                            f'cd {tmp}/.. && cd {tmp} && git push origin main', 'cd - && git push',
                            # shell separators the hook must not skip over
                            'cd .\ngit push origin main', 'cd . & git push --force', 'cd . | git push --force',
                            'git status\ngit push origin main', '(cd . && git push origin main)', '/usr/bin/git push origin main',
                            # git DWIM refs, remotes and config that redirect a push
                            'git push origin heads/main', 'git push origin feature:heads/main', 'git push origin tags/v1.0',
                            'git push https://github.com/x/y.git HEAD:feat',
                            'GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=remote.origin.mirror GIT_CONFIG_VALUE_0=true git push',
                            'git config remote.origin.mirror true', 'git remote add --mirror=push backup /x',
                            "git config alias.ship 'push --force'", 'git config remote.origin.pushurl /x',
                            'git --git-dir /other/.git push origin main', 'git --work-tree=/x push origin feature',
                            'GIT_DIR=/other/.git git push origin feature', 'builtin cd .. && git push origin feature',
                            'popd && git push origin feature', 'eval cd .. && git push origin feature',
                            'export GIT_DIR=/other/.git; git push origin feature',
                            'git push origin main cd', 'git --attr-source HEAD push origin main',
                            'git --some-future-opt value push origin main',
                            'export "GIT_DIR"=/other/.git; git push origin feature']:
                self.assertTrue(self.blocked(command, tmp), command)
            for command in ['git -c core.sshCommand=ssh push origin feature', 'git push -odeploy origin feature',
                            'git push origin feature 2>&1', 'git push origin feature | cat',
                            'git push -u origin feature && git status']:
                self.assertFalse(self.blocked(command, tmp), command)
            subprocess.run(['git', '-C', tmp, 'config', 'remote.origin.mirror', 'true'], check=True)
            self.assertTrue(self.blocked('git push', tmp))
            subprocess.run(['git', '-C', tmp, 'config', '--unset', 'remote.origin.mirror'], check=True)
            for command in ['git -c push.default=matching push', 'git config remote.origin.push refs/heads/*:refs/heads/main',
                            'git config set push.default matching']:
                self.assertTrue(self.blocked(command, tmp), command)
            self.assertFalse(self.blocked('git config --get push.default', tmp))
            subprocess.run(['git', '-C', tmp, 'config', 'push.default', 'matching'], check=True)
            self.assertTrue(self.blocked('git push origin', tmp))
            self.assertFalse(self.blocked('git push origin feature', tmp))
            subprocess.run(['git', '-C', tmp, 'config', 'push.default', 'simple'], check=True)
            subprocess.run(['git', '-C', tmp, 'config', 'remote.origin.push', 'refs/heads/feature:refs/heads/main'], check=True)
            self.assertTrue(self.blocked('git push', tmp))
            self.assertTrue(self.blocked('git push origin feature', tmp))
            self.assertFalse(self.blocked('git push origin feature:feature', tmp))
        with tempfile.TemporaryDirectory() as tmp:
            self.git_repo(tmp, 'main')
            self.assertTrue(self.blocked('git push', tmp))
            self.assertTrue(self.blocked('git push origin @', tmp))
            subprocess.run(['git', '-C', tmp, 'update-ref', 'refs/remotes/upstream/stable', 'HEAD'], check=True)
            subprocess.run(['git', '-C', tmp, 'symbolic-ref', 'refs/remotes/upstream/HEAD', 'refs/remotes/upstream/stable'], check=True)
            self.assertTrue(self.blocked('git push upstream HEAD:stable', tmp))

    def test_rm_rf_allowed_in_sandbox_inside_workdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            for command in ['rm -rf node_modules dist', 'rm -r -f build', 'rm -rf /tmp/agent-work/x']:
                self.assertFalse(self.blocked(command, tmp), command)
            for command in ['rm -rf .', 'rm -rf ..', 'rm -rf ../sibling', 'rm -rf ~', 'rm -rf /', 'rm -rf $DIR/',
                            'rm -rf /home/someone', 'find . -name x | xargs rm -rf', 'rm -rf .git',
                            'rm -rf .git/', 'rm -rf ./.git', 'rm -rf */', 'rm -rf ?*', 'rm -rf /tmp/*',
                            f'cd {tmp}/.. && rm -rf {Path(tmp).name}', 'cd $X && rm -rf build']:
                self.assertTrue(self.blocked(command, tmp), command)
            outside = Path('/etc')
            (Path(tmp) / 'lnk').symlink_to(outside)
            for command in ['rm -rf {/etc,x}', 'rm -rf `pwd`', 'rm -r --forc /home/x', 'rm --recurs dir/../..',
                            'rm -rf lnk/', 'rm -rf lnk/*', 'rm -r .', '/bin/rm -rf /', 'rm -rf .git/objects',
                            'rm -rf $TMPDIR/$(pwd)', 'cd . ; rm -rf ~', 'cd .\nrm -rf /',
                            'TMPDIR=/home && rm -rf $TMPDIR/voreny', 'export TMPDIR=/ ; rm -rf ${TMPDIR}/etc',
                            'builtin cd .. && rm -rf x', 'CDPATH=/ && rm -rf x',
                            'unset TMPDIR; rm -rf $TMPDIR/etc', 'if cd ..; then rm -rf x; fi', '{ cd ..; rm -rf x; }',
                            'rm -rf / cd', 'rm -rf -- / cd',
                            'declare -x TMPDIR=/ ; rm -rf $TMPDIR/etc', 'CDPATH=/home && cd voreny && rm -rf x',
                            # a recursive rm must come first, even after a harmless command
                            'mkdir -p sub && rm -rf sub/out', 'alias rm=x; rm -rf build']:
                self.assertTrue(self.blocked(command, tmp), command)
            for command in ['rm -rf dist/*', 'rm -rf lnk', 'rm -rf .git/rebase-merge', 'git rm -r --cached build',
                            'rm -rf $TMPDIR/scratch', 'rm -rf build && ls', 'mkdir -p out && rm out/x.txt']:
                self.assertFalse(self.blocked(command, tmp), command)
            self.user_settings({'sandbox': {'enabled': False}})
            self.assertTrue(self.blocked('rm -rf node_modules', tmp))
            self.user_settings({'sandbox': {'enabled': True, 'excludedCommands': ['rm *']}})
            self.assertTrue(self.blocked('rm -rf node_modules', tmp))
            self.assertTrue(self.blocked('rm -rf node_modules', tmp, dangerouslyDisableSandbox=True))

    def test_claude_commit_policy(self):
        self.assertEqual(self.hook('validate-commit.py', 'git commit -m hello')['decision'], 'block')
        self.assertEqual(self.hook('validate-commit.py', 'git commit')['decision'], 'block')
        self.assertIsNone(self.hook('validate-commit.py', 'git commit --fixup=abc123'))
        # Attribution is left to the agent; any -F message passes.
        self.assertIsNone(self.hook('validate-commit.py', 'git commit -F message'))

    def test_handoff_auto_allow_stays_inside_the_handoffs_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            handoffs = home / '.local/agent-handoffs'
            (handoffs / 'repo').mkdir(parents=True)
            (handoffs / 'escape').symlink_to(home)
            def allowed(path):
                payload = {'tool_name': 'Read', 'tool_input': {'file_path': str(path)}}
                result = subprocess.run(['bash', str(ROOT / 'home/.claude/hooks/auto-allow-handoffs.sh')], input=json.dumps(payload), text=True, capture_output=True, check=True, env={**os.environ, 'HOME': tmp})
                return bool(result.stdout) and json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'] == 'allow'
            self.assertTrue(allowed(handoffs / 'repo/new-handoff.md'))
            self.assertFalse(allowed(handoffs / '../../.ssh/id_ed25519'))
            self.assertFalse(allowed(handoffs / 'escape/.ssh/id_ed25519'))
            self.assertFalse(allowed(home / 'elsewhere/.local/agent-handoffs/x.md'))
            self.assertFalse(allowed(handoffs))

class CodexTests(unittest.TestCase):
    def codex_hook(self, command, cwd=''):
        payload = {'hook_event_name': 'PreToolUse', 'tool_name': 'Bash',
                   'tool_input': {'command': command}, 'cwd': cwd}
        result = subprocess.run(['python3', str(ROOT / 'home/.codex/hooks/agent-policy.py')], input=json.dumps(payload), text=True, capture_output=True, check=True)
        return json.loads(result.stdout) if result.stdout else None

    def test_codex_shares_command_policy_without_claude_sandbox_flag(self):
        self.assertEqual(self.codex_hook('git push origin main')['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.codex_hook('rm -rf scratch')['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.codex_hook('git commit -m hello')['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertIsNone(self.codex_hook('git commit -F message'))
        self.assertIsNone(self.codex_hook('npx playwright test'))

if __name__ == '__main__':
    unittest.main()
