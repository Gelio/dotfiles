import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { sandbox, runEngine, linkCfg, makeRepo } from './helpers.ts';

const CFG = `export default { ports: { UI: 3003 }, symlinkTargets: ['README.md'] };`;
const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

test('list shows main row + worktree row', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/list1'], { configHome });
  const { out } = runEngine(repo, ['list'], { configHome });
  assert.match(out, /BRANCH/);
  assert.match(out, /\(main\)/);
  assert.match(out, /feature-list1/);
});

test('list --all spans registered repos', () => {
  const { root, configHome } = sandbox();
  const r1 = makeRepo(path.join(root, 'r1'));
  const r2 = makeRepo(path.join(root, 'r2'));
  fs.writeFileSync(path.join(root, 'c1.mts'), CFG);
  fs.writeFileSync(path.join(root, 'c2.mts'), CFG);
  fs.symlinkSync(path.join(root, 'c1.mts'), path.join(r1, '.worktrees.mts'));
  fs.symlinkSync(path.join(root, 'c2.mts'), path.join(r2, '.worktrees.mts'));
  runEngine(r1, ['setup', 'feature/p'], { configHome });
  runEngine(r2, ['setup', 'feature/q'], { configHome });
  const { out } = runEngine(r1, ['list', '--all'], { configHome });
  assert.match(out, new RegExp(esc(r1)));
  assert.match(out, new RegExp(esc(r2)));
});

test('list --all survives a registered repo with a missing config', () => {
  const { root, configHome } = sandbox();
  const good = makeRepo(path.join(root, 'good'));
  const broken = makeRepo(path.join(root, 'broken'));
  fs.writeFileSync(path.join(root, 'good.mts'), CFG);
  fs.symlinkSync(path.join(root, 'good.mts'), path.join(good, '.worktrees.mts'));
  // good repo registers itself + creates a worktree
  runEngine(good, ['setup', 'feature/ok'], { configHome });
  // Manually register the broken repo (no config resolvable for it) by
  // appending to the registry the same way the engine would.
  const reg = path.join(configHome, 'registry');
  fs.appendFileSync(reg, `${broken}\t${path.join(broken, '.worktrees.mts')}\n`);
  const { out, code } = runEngine(good, ['list', '--all'], { configHome });
  assert.equal(code, 0);                       // did NOT abort the whole run
  assert.match(out, /feature-ok/);             // good repo still rendered
  assert.match(out, /config error/);           // broken repo reported, not fatal
});
