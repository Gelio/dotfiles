import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { sandbox, runEngine, linkCfg, writeCentralConfig } from './helpers.ts';
import { configPathIsSafe, repoKey } from '../src/config.ts';

test('configPathIsSafe: outside symlink ok; inside/plain refused', () => {
  const { root, repo } = sandbox();
  const f = path.join(repo, '.worktrees.mts');
  fs.writeFileSync(path.join(root, 'real.mts'), 'export default {}');
  fs.symlinkSync(path.join(root, 'real.mts'), f);
  assert.equal(configPathIsSafe(repo, f), true);
  fs.writeFileSync(path.join(repo, 'evil.mts'), 'export default {}');
  fs.rmSync(f);
  fs.symlinkSync('./evil.mts', f);
  assert.equal(configPathIsSafe(repo, f), false);
  fs.rmSync(f);
  fs.writeFileSync(f, 'export default {}');
  assert.equal(configPathIsSafe(repo, f), false);
});

const OK_CFG = `export default { symlinkTargets: ['README.md'] };\n`;

test('discovery: outside symlink accepted (_config reports it)', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, OK_CFG);
  const { out, code } = runEngine(repo, ['_config'], { configHome });
  assert.equal(code, 0);
  assert.match(out, /\.worktrees\.mts/);
});

test('discovery: plain file refused, points at init', () => {
  const { repo, configHome } = sandbox();
  fs.writeFileSync(path.join(repo, '.worktrees.mts'), OK_CFG);
  const { out, code } = runEngine(repo, ['_config'], { configHome });
  assert.notEqual(code, 0);
  assert.match(out, /worktrees init/);
});

test('discovery: plain-JS central config (.mjs) loads', () => {
  const { repo, configHome } = sandbox();
  const key = repoKey(repo);
  writeCentralConfig(
    configHome,
    repo,
    `export default { symlinkTargets: ['README.md'] };\n`,
    '.mjs',
  );
  const { out, code } = runEngine(repo, ['_config'], { configHome });
  assert.equal(code, 0);
  assert.match(out, new RegExp(`${key}\\.mjs`));
});

test('discovery: central fallback + de-duped registry', () => {
  const { repo, configHome } = sandbox();
  writeCentralConfig(configHome, repo, OK_CFG);
  assert.equal(runEngine(repo, ['_config'], { configHome }).code, 0);
  runEngine(repo, ['_config'], { configHome });
  const reg = fs.readFileSync(path.join(configHome, 'registry'), 'utf8');
  assert.equal(reg.split('\n').filter((l) => l.startsWith(repo + '\t')).length, 1);
});
