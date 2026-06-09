import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sandbox, runEngine, linkCfg } from './helpers.ts';

const CFG = `export default { symlinkTargets: ['README.md'] };`;

test('completes subcommands when no subcommand typed', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  const { out, code } = runEngine(repo, ['__complete', ''], { configHome });
  assert.equal(code, 0);
  for (const s of ['setup', 'teardown', 'list', 'sync', 'init'])
    assert.match(out, new RegExp(`^${s}$`, 'm'));
});

test('setup --from completes git refs (local + remote)', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/x'], { configHome });
  const { out } = runEngine(repo, ['__complete', 'setup', '--from', ''], { configHome });
  assert.deepEqual(
    out.trim().split('\n').toSorted(),
    ['feature/x', 'main', 'origin/main'].toSorted(),
  );
});

test('setup positional offers the --from flag, not refs', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  const { out } = runEngine(repo, ['__complete', 'setup', ''], { configHome });
  assert.match(out, /^--from$/m);
  assert.doesNotMatch(out, /origin\/main/);
});

test('teardown completes existing worktree dir names', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/x'], { configHome });
  const { out } = runEngine(repo, ['__complete', 'teardown', ''], { configHome });
  assert.match(out, /^feature-x$/m);
});

test('teardown offers nothing for a flag-like current word', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/x'], { configHome });
  const { out } = runEngine(repo, ['__complete', 'teardown', '-'], { configHome });
  assert.equal(out.trim(), '');
});

test('list completes --all', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  const { out } = runEngine(repo, ['__complete', 'list', ''], { configHome });
  assert.match(out, /^--all$/m);
});

test('init completes --in-repo', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  const { out } = runEngine(repo, ['__complete', 'init', ''], { configHome });
  assert.match(out, /^--in-repo$/m);
});

test('completion is silent and exits 0 outside a git repo', (t) => {
  const { root, configHome } = sandbox(t);
  // `root` (the mkdtemp dir) is not itself a git repo — only root/repo is.
  const { out, code } = runEngine(root, ['__complete', 'teardown', ''], { configHome });
  assert.equal(code, 0);
  assert.equal(out.trim(), '');
});

test('setup --from is silent outside a git repo', (t) => {
  const { root, configHome } = sandbox(t);
  const { out, code } = runEngine(root, ['__complete', 'setup', '--from', ''], { configHome });
  assert.equal(code, 0);
  assert.equal(out.trim(), '');
});
