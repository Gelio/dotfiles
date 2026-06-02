import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sandbox, runEngine } from './helpers.ts';

test('no args prints usage, exits non-zero', () => {
  const { repo, configHome } = sandbox();
  const { out, code } = runEngine(repo, [], { configHome });
  assert.notEqual(code, 0);
  assert.match(out, /Usage:/);
});

test('unknown subcommand exits non-zero', () => {
  const { repo, configHome } = sandbox();
  const { out, code } = runEngine(repo, ['frobnicate'], { configHome });
  assert.notEqual(code, 0);
  assert.match(out, /Unknown subcommand/);
});
