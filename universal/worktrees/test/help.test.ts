import { test } from 'node:test';
import assert from 'node:assert/strict';
import { sandbox, runEngine } from './helpers.ts';

// Every user-facing subcommand should print its own help and exit cleanly for
// both -h and --help, without needing a configured repo.
const SUBCOMMANDS = ['setup', 'teardown', 'list', 'sync', 'init', 'config-path'];

for (const sub of SUBCOMMANDS) {
  for (const flag of ['-h', '--help']) {
    test(`${sub} ${flag} prints help and exits 0`, (t) => {
      const { repo, configHome } = sandbox(t);
      const { out, code } = runEngine(repo, [sub, flag], { configHome });
      assert.equal(code, 0);
      assert.match(out, new RegExp(`Usage: worktrees ${sub}\\b`));
      assert.match(out, /-h, --help/);
    });
  }
}

test('help is shown even when required positionals are missing', (t) => {
  const { repo, configHome } = sandbox(t);
  // `setup` normally errors without a <branch>; --help must short-circuit that.
  const { out, code } = runEngine(repo, ['setup', '--help'], { configHome });
  assert.equal(code, 0);
  assert.doesNotMatch(out, /usage: worktrees setup <branch>/); // not the die() path
  assert.match(out, /--from/);
});

test('help takes precedence over otherwise-valid arguments', (t) => {
  const { repo, configHome } = sandbox(t);
  const { out, code } = runEngine(repo, ['setup', 'my-branch', '-h'], { configHome });
  assert.equal(code, 0);
  assert.match(out, /Usage: worktrees setup\b/);
});
