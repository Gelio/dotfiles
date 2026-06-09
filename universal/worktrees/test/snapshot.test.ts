import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sandbox, runEngine } from './helpers.ts';

// Snapshot tests pin the EXACT text of fully deterministic CLI output, so any
// accidental drift in wording/layout is caught by `npm test`. We deliberately
// only snapshot output that contains no environment-specific data (no temp-dir
// paths, no git hashes), so no normalization is needed here. Regenerate with
// `npm run test:update-snapshots` after an intentional change.

test('no-args usage text', (t) => {
  const { repo, configHome } = sandbox(t);
  const { out, code } = runEngine(repo, [], { configHome });
  assert.notEqual(code, 0);
  t.assert.snapshot(out);
});

test('top-level subcommand completion listing', (t) => {
  const { repo, configHome } = sandbox(t);
  const { out, code } = runEngine(repo, ['__complete', ''], { configHome });
  assert.equal(code, 0);
  t.assert.snapshot(out);
});
