import { test } from 'node:test';
import assert from 'node:assert/strict';
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

test('setup creates worktree, computes ports, runs hook + summary', () => {
  const { root, repo, configHome } = sandbox();
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

test('setup idempotent: reuses index, no duplicate registry entry', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, HOOK_CFG);
  runEngine(repo, ['setup', 'feature/a'], { configHome });
  runEngine(repo, ['setup', 'feature/b'], { configHome });
  const { out } = runEngine(repo, ['setup', 'feature/a'], { configHome });
  assert.match(out, /Existing port index/);
  const reg = fs.readFileSync(path.join(repo, 'worktrees', '.port-registry'), 'utf8');
  assert.equal(reg.split('\n').filter((l) => l.startsWith('feature-a:')).length, 1);
});

test('setup with no ports skips the port-registry', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, `export default { symlinkTargets: ['README.md'] };`);
  assert.equal(runEngine(repo, ['setup', 'feature/y'], { configHome }).code, 0);
  assert.equal(fs.existsSync(path.join(repo, 'worktrees', '.port-registry')), false);
});
