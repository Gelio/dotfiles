import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
import { $ } from 'zx';
import { readPortRegistry } from '../ports.ts';

/**
 * Run git quietly, returning trimmed stdout, or null on non-zero exit. `quiet`
 * suppresses git's own stderr (e.g. "fatal: not a git repository") so it never
 * pollutes the completion output the shell parses.
 */
async function gitQuiet(args: string[]): Promise<string | null> {
  const p = await $({ quiet: true })`git ${args}`.nothrow();
  return p.exitCode === 0 ? p.stdout.trim() : null;
}

const SUBCOMMANDS = ['setup', 'teardown', 'list', 'sync', 'init'];

// Flags each subcommand accepts. Used both to offer flags and to drop ones
// already present on the line.
const FLAGS: Record<string, string[]> = {
  setup: ['--from'],
  list: ['--all'],
  init: ['--in-repo'],
  teardown: [],
  sync: [],
};

/** Repo toplevel, or null if not inside a git repo. */
async function safeRepoRoot(): Promise<string | null> {
  return gitQuiet(['rev-parse', '--show-toplevel']);
}

/** Local + remote branch names, for `setup --from <base>`. Empty outside a repo. */
async function refs(): Promise<string[]> {
  const out = await gitQuiet(['for-each-ref', '--format=%(refname:short)', 'refs/heads', 'refs/remotes']);
  if (out === null) return [];
  return out.split('\n').map((s) => s.trim()).filter(Boolean);
}

/** Existing worktree dir names under `<repo>/worktrees/` — the arg `teardown` resolves. */
async function worktreeNames(): Promise<string[]> {
  const repo = await safeRepoRoot();
  if (!repo) return [];
  const names = new Set<string>();
  for (const name of (await readPortRegistry(repo)).keys()) names.add(name);
  try {
    const entries = await fsp.readdir(path.join(repo, 'worktrees'), { withFileTypes: true });
    for (const e of entries) if (e.isDirectory()) names.add(e.name);
  } catch {
    /* no worktrees dir yet */
  }
  return [...names];
}

/** Flags for `sub` not already typed in `typed` (the args between the subcommand and the cursor). */
function remainingFlags(sub: string, typed: string[]): string[] {
  return (FLAGS[sub] ?? []).filter((f) => !typed.includes(f));
}

async function computeCandidates(words: string[]): Promise<string[]> {
  // `words` is everything after `worktrees`; the last element is the current
  // (possibly empty) word being completed. The shell does prefix filtering.
  if (words.length <= 1) return SUBCOMMANDS;
  const sub = words[0];
  const cur = words[words.length - 1] ?? '';
  const prev = words[words.length - 2] ?? '';
  const typed = words.slice(1, -1); // args already entered, minus the current word

  switch (sub) {
    case 'setup':
      return prev === '--from' ? refs() : remainingFlags('setup', typed);
    case 'teardown':
      return cur.startsWith('-') ? [] : worktreeNames();
    case 'list':
      return remainingFlags('list', typed);
    case 'init':
      return remainingFlags('init', typed);
    default:
      return [];
  }
}

/**
 * Print shell-completion candidates (one per line) for a partial command line.
 * Always exits cleanly with no output on error — shells call this on every Tab.
 */
export async function cmdComplete(argv: string[]): Promise<void> {
  try {
    const candidates = await computeCandidates(argv);
    if (candidates.length) console.log(candidates.join('\n'));
  } catch {
    /* completion stays silent */
  }
}
