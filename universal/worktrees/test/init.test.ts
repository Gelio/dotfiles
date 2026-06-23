import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { sandbox, runEngine } from './helpers.ts';
import { repoKey } from '../src/config.ts';

test('init (central) scaffolds a typed config + registers', (t) => {
  const { repo, configHome } = sandbox(t);
  const { out } = runEngine(repo, ['init'], { configHome });
  const dest = path.join(configHome, 'repos', `${repoKey(repo)}.mts`);
  assert.equal(fs.existsSync(dest), true);
  const body = fs.readFileSync(dest, 'utf8');
  assert.match(body, /WorktreesConfig/);
  assert.match(body, /postCreate/);
  assert.match(out, new RegExp(`repos.${repoKey(repo)}\\.mts`));
});

test('init (central) is idempotent: second run leaves config untouched', (t) => {
  const { repo, configHome } = sandbox(t);
  runEngine(repo, ['init'], { configHome });
  const { out, code } = runEngine(repo, ['init'], { configHome });
  assert.equal(code, 0);
  assert.match(out, /Config already exists/);
});
