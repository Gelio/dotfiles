import * as path from 'node:path';
import { die } from '../log.ts';
import { git, gitOk } from '../git.ts';
import { loadConfig } from '../config.ts';
import { removePortRegistryEntry } from '../ports.ts';
import { ask } from '../prompt.ts';

function isYes(s: string): boolean {
  return /^y$/i.test(s.trim());
}

async function dirExists(p: string): Promise<boolean> {
  try {
    await (await import('node:fs/promises')).stat(p);
    return true;
  } catch {
    return false;
  }
}

export async function cmdTeardown(argv: string[]): Promise<void> {
  const name = argv[0];
  if (!name) die('usage: worktrees teardown <name|branch>');
  const { repo } = await loadConfig();
  const dirName = name.replace(/\//g, '-');
  const wt = path.join(repo, 'worktrees', dirName);
  if (!(await dirExists(wt))) die(`worktree directory not found: ${wt}`);

  console.log(`This will remove worktree at: ${wt}`);
  if (!isYes(await ask('Continue? [y/N] '))) {
    console.log('Aborted.');
    process.exit(0);
  }

  let branch = '';
  try {
    branch = await git(['branch', '--show-current'], wt);
  } catch {
    /* ignore */
  }

  console.log('Removing worktree...');
  await git(['worktree', 'remove', '--force', wt]);
  await removePortRegistryEntry(repo, dirName);
  console.log(`Removed port registry entry for ${dirName}`);

  if (branch) {
    if (isYes(await ask(`Delete branch '${branch}'? [y/N] `))) {
      if (!(await gitOk(['branch', '-D', branch]))) console.log(`Could not delete branch ${branch}`);
    }
  }
  await git(['worktree', 'prune']);
  console.log('Done. Worktree removed and pruned.');
}
