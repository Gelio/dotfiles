import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { sandbox, runEngine, linkCfg } from './helpers.ts';

const CFG = `export default { ports: { UI: 3003 }, symlinkTargets: ['README.md'] };`;

test('teardown removes worktree + registry entry (y, then n)', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/gone'], { configHome });
  assert.equal(fs.existsSync(path.join(repo, 'worktrees', 'feature-gone')), true);
  runEngine(repo, ['teardown', 'feature/gone'], { configHome, input: 'y\nn\n' });
  assert.equal(fs.existsSync(path.join(repo, 'worktrees', 'feature-gone')), false);
  const reg = fs.readFileSync(path.join(repo, 'worktrees', '.port-registry'), 'utf8');
  assert.equal(reg.split('\n').filter((l) => l.startsWith('feature-gone:')).length, 0);
});

test('teardown aborts on N', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/stay'], { configHome });
  runEngine(repo, ['teardown', 'feature/stay'], { configHome, input: 'n\n' });
  assert.equal(fs.existsSync(path.join(repo, 'worktrees', 'feature-stay')), true);
});
