import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { sandbox, runEngine, writeCfg, writeCentralConfig } from './helpers.ts';
import { repoKey } from '../src/config.ts';

const OK_CFG = `export default { symlinkTargets: ['README.md'] };\n`;

test('discovery: central config accepted (_config reports it)', (t) => {
  const { root, repo, configHome } = sandbox(t);
  writeCfg(root, repo, OK_CFG);
  const { out, code } = runEngine(repo, ['_config'], { configHome });
  assert.equal(code, 0);
  assert.match(out, new RegExp(`repos.${repoKey(repo)}\\.mts`));
});

test('discovery: an in-repo .worktrees.* is ignored, points at init', (t) => {
  const { repo, configHome } = sandbox(t);
  // Only the central config is consulted; a file inside the repo is never read.
  fs.writeFileSync(path.join(repo, '.worktrees.mts'), OK_CFG);
  const { out, code } = runEngine(repo, ['_config'], { configHome });
  assert.notEqual(code, 0);
  assert.match(out, /worktrees init/);
});

test('discovery: plain-JS central config (.mjs) loads', (t) => {
  const { repo, configHome } = sandbox(t);
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

test('loading: a config with a syntax error fails loudly (no exit 0, no hang)', (t) => {
  const { root, repo, configHome } = sandbox(t);
  // Unterminated object literal -> the dynamic import() throws while parsing.
  writeCfg(root, repo, 'export default { ports: {\n');
  const { out, code } = runEngine(repo, ['_config'], { configHome });
  // The entry's main().catch() surfaces the import failure as a readable
  // `Error: ...` line and exits non-zero, rather than hanging or swallowing it.
  assert.notEqual(code, 0);
  assert.match(out, /Error:/);
  assert.match(out, /Unexpected token/);
});

test('discovery: central fallback + de-duped registry', (t) => {
  const { repo, configHome } = sandbox(t);
  writeCentralConfig(configHome, repo, OK_CFG);
  assert.equal(runEngine(repo, ['_config'], { configHome }).code, 0);
  runEngine(repo, ['_config'], { configHome });
  const reg = fs.readFileSync(path.join(configHome, 'registry'), 'utf8');
  assert.equal(reg.split('\n').filter((l) => l.startsWith(repo + '\t')).length, 1);
});
