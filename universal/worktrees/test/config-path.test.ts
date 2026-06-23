import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sandbox, runEngine, writeCentralConfig } from './helpers.ts';

const CFG = 'export default { symlinkTargets: [] };\n';

test('config-path prints the central config path', (t) => {
  const { repo, configHome } = sandbox(t);
  const dest = writeCentralConfig(configHome, repo, CFG);
  const { out, code } = runEngine(repo, ['config-path'], { configHome });
  assert.equal(code, 0);
  assert.equal(out.trim(), dest);
});

test('config-path with no config exits non-zero', (t) => {
  const { repo, configHome } = sandbox(t);
  const { out, code } = runEngine(repo, ['config-path'], { configHome });
  assert.notEqual(code, 0);
  assert.match(out, /no worktrees config/);
});
