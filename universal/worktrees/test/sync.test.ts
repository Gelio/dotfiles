import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
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

test('sync re-applies symlinks and runs postSync (select all)', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/syncme'], { configHome });
  const wt = path.join(repo, 'worktrees', 'feature-syncme');
  fs.rmSync(path.join(wt, 'README.md')); // break symlink
  runEngine(repo, ['sync'], { configHome, input: 'a\n' });
  assert.equal(fs.lstatSync(path.join(wt, 'README.md')).isSymbolicLink(), true);
  assert.equal(fs.existsSync(path.join(wt, '.post_sync_ran')), true);
});

test('sync numeric selection syncs only the chosen index, reports invalid token', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  // Two worktrees: order in the registry/list is creation order (a, then b).
  runEngine(repo, ['setup', 'feature/a'], { configHome });
  runEngine(repo, ['setup', 'feature/b'], { configHome });
  const wtA = path.join(repo, 'worktrees', 'feature-a');
  const wtB = path.join(repo, 'worktrees', 'feature-b');
  const { out } = runEngine(repo, ['sync'], { configHome, input: '2 bogus\n' });
  assert.match(out, /Invalid selection: bogus/);
  // Only the SECOND worktree was synced (postSync marker present on b, not a).
  assert.equal(fs.existsSync(path.join(wtB, '.post_sync_ran')), true);
  assert.equal(fs.existsSync(path.join(wtA, '.post_sync_ran')), false);
});

test('sync empty selection syncs nothing', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/only'], { configHome });
  const wt = path.join(repo, 'worktrees', 'feature-only');
  const { out } = runEngine(repo, ['sync'], { configHome, input: '\n' });
  assert.match(out, /No worktrees selected\./);
  assert.equal(fs.existsSync(path.join(wt, '.post_sync_ran')), false);
});

test('sync skips a worktree with unstaged tracked changes', (t) => {
  const { root, repo, configHome } = sandbox(t);
  linkCfg(root, repo, CFG);
  runEngine(repo, ['setup', 'feature/dirty'], { configHome });
  const wt = path.join(repo, 'worktrees', 'feature-dirty');
  // README.md is a symlink (a symlinkTarget); modify a real tracked file
  // instead. The worktree branches off main which has README.md committed via
  // the worktree's own checkout — write to a tracked file present in HEAD.
  // The repo's committed tracked file is README.md, but in the worktree it is a
  // symlink. Create+commit a tracked file in the worktree, then modify it so
  // `git diff --diff-filter=M --quiet` fails.
  const tracked = path.join(wt, 'tracked.txt');
  fs.writeFileSync(tracked, 'original\n');
  const git = (...a: string[]) => spawnSync('git', ['-C', wt, ...a], { encoding: 'utf8' });
  git('add', 'tracked.txt');
  git('commit', '-qm', 'add tracked');
  fs.writeFileSync(tracked, 'MODIFIED\n');
  const { out } = runEngine(repo, ['sync'], { configHome, input: 'a\n' });
  assert.match(out, /WARNING/);
  assert.match(out, /skipping/);
  // reset --hard did NOT run: the modification survives.
  assert.equal(fs.readFileSync(tracked, 'utf8'), 'MODIFIED\n');
  assert.equal(fs.existsSync(path.join(wt, '.post_sync_ran')), false);
});
