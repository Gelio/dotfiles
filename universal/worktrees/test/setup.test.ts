import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { sandbox, runEngine, linkCfg } from './helpers.ts';

const HOOK_CFG = `export default {
  ports: { UI: 3003 },
  portStep: 10,
  symlinkTargets: ['README.md'],
  async postCreate({ wt, ports }) {
    console.log('HOOK ui=' + ports.UI);
    await (await import('node:fs/promises')).writeFile(wt + '/.post_create_ran', '');
  },
  summary({ ports }) { return 'SUMMARY ui=' + ports.UI; },
};`;

test('setup creates worktree, computes ports, runs hook + summary', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, HOOK_CFG);
  const { out, code } = runEngine(repo, ['setup', 'feature/abc', '--from', 'main'], { configHome });
  assert.equal(code, 0);
  const wt = path.join(repo, 'worktrees', 'feature-abc');
  assert.equal(fs.existsSync(wt), true);
  assert.equal(fs.existsSync(path.join(wt, '.post_create_ran')), true);
  assert.match(out, /ui=3013/);
  assert.match(out, /SUMMARY ui=3013/);
  assert.equal(fs.lstatSync(path.join(wt, 'README.md')).isSymbolicLink(), true);
});

test('setup idempotent: reuses index, no duplicate registry entry', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, HOOK_CFG);
  runEngine(repo, ['setup', 'feature/a'], { configHome });
  runEngine(repo, ['setup', 'feature/b'], { configHome });
  const { out } = runEngine(repo, ['setup', 'feature/a'], { configHome });
  assert.match(out, /Existing port index/);
  const reg = fs.readFileSync(path.join(repo, 'worktrees', '.port-registry'), 'utf8');
  assert.equal(reg.split('\n').filter((l) => l.startsWith('feature-a:')).length, 1);
});

test('setup with no ports skips the port-registry', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, `export default { symlinkTargets: ['README.md'] };`);
  assert.equal(runEngine(repo, ['setup', 'feature/y'], { configHome }).code, 0);
  assert.equal(fs.existsSync(path.join(repo, 'worktrees', '.port-registry')), false);
});

test('setup warns and skips a symlinkTarget whose source is missing', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, `export default { symlinkTargets: ['does-not-exist'] };`);
  const { out, code } = runEngine(repo, ['setup', 'feature/missing'], { configHome });
  assert.equal(code, 0);
  assert.match(out, /Warning:/);
  assert.match(out, /skipping symlink/);
  // Nothing was created at the missing target.
  assert.equal(
    fs.existsSync(path.join(repo, 'worktrees', 'feature-missing', 'does-not-exist')),
    false,
  );
});

test('setup merge-symlinks a configured dir and reports tracked collisions', (t) => {
  const { root, repo, configHome } = sandbox(t);
  // Commit a .claude/ dir with two files into the repo so the worktree checks
  // them out as REAL tracked files; the main repo's .claude/ is the merge src.
  fs.mkdirSync(path.join(repo, '.claude'), { recursive: true });
  fs.writeFileSync(path.join(repo, '.claude', 'settings.json'), '{}\n');
  fs.writeFileSync(path.join(repo, '.claude', 'notes.md'), 'notes\n');
  const g = (...a: string[]) => spawnSync('git', ['-C', repo, ...a], { encoding: 'utf8' });
  g('add', '-A');
  g('commit', '-qm', 'add .claude');
  g('update-ref', 'refs/remotes/origin/main', 'HEAD');
  linkCfg(root, repo, `export default { mergeSymlinkDirs: ['.claude'] };`);
  const { out, code } = runEngine(repo, ['setup', 'feature/merge'], { configHome });
  assert.equal(code, 0);
  const wt = path.join(repo, 'worktrees', 'feature-merge');
  // Tracked files in the worktree's checkout are preserved (real, not symlinked)
  // and reported.
  assert.match(out, /Tracked \.claude files \(not symlinked\):/);
  assert.equal(fs.lstatSync(path.join(wt, '.claude', 'settings.json')).isSymbolicLink(), false);
});

test('setup merge-symlinks a new dir entry (no tracked collision)', (t) => {
  const { root, repo, configHome } = sandbox(t);
  // .claude/ exists ONLY in the main repo (not committed) -> the worktree has
  // no real .claude, so every entry gets symlinked through the merge loop.
  fs.mkdirSync(path.join(repo, '.claude'), { recursive: true });
  fs.writeFileSync(path.join(repo, '.claude', 'config.json'), '{}\n');
  linkCfg(root, repo, `export default { mergeSymlinkDirs: ['.claude'] };`);
  const { code } = runEngine(repo, ['setup', 'feature/mergenew'], { configHome });
  assert.equal(code, 0);
  const link = path.join(repo, 'worktrees', 'feature-mergenew', '.claude', 'config.json');
  assert.equal(fs.lstatSync(link).isSymbolicLink(), true);
});
