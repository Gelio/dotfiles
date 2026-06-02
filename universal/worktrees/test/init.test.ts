import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { sandbox, runEngine } from './helpers.ts';
import { repoKey } from '../src/config.ts';

test('init (central) scaffolds a typed config + registers', () => {
  const { repo, configHome } = sandbox();
  const { out } = runEngine(repo, ['init'], { configHome });
  const dest = path.join(configHome, 'repos', `${repoKey(repo)}.mts`);
  assert.equal(fs.existsSync(dest), true);
  const body = fs.readFileSync(dest, 'utf8');
  assert.match(body, /WorktreesConfig/);
  assert.match(body, /postCreate/);
  assert.match(out, new RegExp(`repos.${repoKey(repo)}\\.mts`));
});

test('init --in-repo appends exclude idempotently + prints guidance', () => {
  const { repo, configHome } = sandbox();
  runEngine(repo, ['init', '--in-repo'], { configHome });
  runEngine(repo, ['init', '--in-repo'], { configHome });
  const ex = fs.readFileSync(path.join(repo, '.git', 'info', 'exclude'), 'utf8');
  assert.equal(ex.split('\n').filter((l) => l === '.worktrees.mts').length, 1);
  const { out } = runEngine(repo, ['init', '--in-repo'], { configHome });
  assert.match(out, /ln -s/);
});
