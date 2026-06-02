import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { sandbox, runEngine, linkCfg } from './helpers.ts';

const CFG = `export default {
  ports: { UI: 3003 },
  symlinkTargets: ['README.md'],
  async postSync({ wt }) {
    await (await import('node:fs/promises')).writeFile(wt + '/.post_sync_ran', '');
  },
};`;

test('sync re-applies symlinks and runs postSync (select all)', () => {
  const { root, repo, configHome } = sandbox();
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/syncme'], { configHome });
  const wt = path.join(repo, 'worktrees', 'feature-syncme');
  fs.rmSync(path.join(wt, 'README.md')); // break symlink
  runEngine(repo, ['sync'], { configHome, input: 'a\n' });
  assert.equal(fs.lstatSync(path.join(wt, 'README.md')).isSymbolicLink(), true);
  assert.equal(fs.existsSync(path.join(wt, '.post_sync_ran')), true);
});
