import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sandbox, runEngine, linkCfg } from './helpers.ts';

const CFG = `export default { symlinkTargets: ['README.md'] };`;

test('completes subcommands when no subcommand typed', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, CFG);
  const { out, code } = runEngine(repo, ['__complete', ''], { configHome });
  assert.equal(code, 0);
  for (const s of ['setup', 'teardown', 'list', 'sync', 'init'])
    assert.match(out, new RegExp(`^${s}$`, 'm'));
});

test('setup --from completes git refs (local + remote)', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/x'], { configHome });
  const { out } = runEngine(repo, ['__complete', 'setup', '--from', ''], { configHome });
  assert.match(out, /^main$/m);
  assert.match(out, /^origin\/main$/m);
  assert.match(out, /^feature\/x$/m);
});

test('setup positional offers the --from flag, not refs', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, CFG);
  const { out } = runEngine(repo, ['__complete', 'setup', ''], { configHome });
  assert.match(out, /^--from$/m);
  assert.doesNotMatch(out, /origin\/main/);
});

test('teardown completes existing worktree dir names', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/x'], { configHome });
  const { out } = runEngine(repo, ['__complete', 'teardown', ''], { configHome });
  assert.match(out, /^feature-x$/m);
});

test('teardown offers nothing for a flag-like current word', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/x'], { configHome });
  const { out } = runEngine(repo, ['__complete', 'teardown', '-'], { configHome });
  assert.equal(out.trim(), '');
});

test('list completes --all', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, CFG);
  const { out } = runEngine(repo, ['__complete', 'list', ''], { configHome });
  assert.match(out, /^--all$/m);
});

test('init completes --in-repo', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, CFG);
  const { out } = runEngine(repo, ['__complete', 'init', ''], { configHome });
  assert.match(out, /^--in-repo$/m);
});

test('completion is silent and exits 0 outside a git repo', () => {
  const { root, configHome } = sandbox();
  // `root` (the mkdtemp dir) is not itself a git repo — only root/repo is.
  const { out, code } = runEngine(root, ['__complete', 'teardown', ''], { configHome });
  assert.equal(code, 0);
  assert.equal(out.trim(), '');
});

test('setup --from is silent outside a git repo', () => {
  const { root, configHome } = sandbox();
  const { out, code } = runEngine(root, ['__complete', 'setup', '--from', ''], { configHome });
  assert.equal(code, 0);
  assert.equal(out.trim(), '');
});
