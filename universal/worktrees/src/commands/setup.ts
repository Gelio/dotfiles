import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
import { parseArgs } from 'node:util';
import { $, chalk, spinner } from 'zx';
import type { HookContext } from '../types.ts';
import { die, ok } from '../log.ts';
import { git, addRepoExclude } from '../git.ts';
import { loadConfig } from '../config.ts';
import {
  appendPortRegistry,
  computePorts,
  hasPorts,
  nextIndex,
  readPortRegistry,
} from '../ports.ts';
import { applySymlinks, symlinkInfoExclude } from '../symlinks.ts';

export async function cmdSetup(argv: string[]): Promise<void> {
  const { values, positionals } = parseArgs({
    args: argv,
    options: { from: { type: 'string' } },
    allowPositionals: true,
  });
  const branch = positionals[0];
  if (!branch) die('usage: worktrees setup <branch> [--from <base>]');
  const base = values.from ?? 'origin/main';

  const { config, repo } = await loadConfig();
  const dirName = branch.replace(/\//g, '-');
  const wt = path.join(repo, 'worktrees', dirName);
  await fsp.mkdir(path.join(repo, 'worktrees'), { recursive: true });
  // Keep the worktree base dir out of the main repo's git status. The pattern is
  // root-anchored + dir-only because the tree always lives at <repo>/worktrees/.
  // symlinkInfoExclude shares this file into each worktree, so one entry covers all.
  await addRepoExclude(repo, '/worktrees/');

  if (await dirExists(wt)) {
    console.log(`Worktree already exists at ${wt} — updating configuration...`);
  } else {
    await spinner(`Creating worktree at ${wt} (branch: ${branch}, base: ${base})`, () =>
      git(['worktree', 'add', '-b', branch, wt, base]),
    );
  }

  let ports: Record<string, number> = {};
  if (hasPorts(config)) {
    const reg = await readPortRegistry(repo);
    let idx = reg.get(dirName);
    if (idx === undefined) {
      idx = nextIndex(reg);
      await appendPortRegistry(repo, dirName, idx);
      console.log(`Allocated port index: ${idx}`);
    } else {
      console.log(`Existing port index: ${idx}`);
    }
    ports = computePorts(config, idx);
  }

  await applySymlinks(repo, wt, config);
  console.log('Symlinks applied');
  await symlinkInfoExclude(repo, wt);
  console.log('Symlinked info/exclude');

  let branchNow = branch;
  try {
    branchNow = (await git(['branch', '--show-current'], wt)) || branch;
  } catch {
    /* detached/new */
  }
  const ctx: HookContext = { wt, mainRepo: repo, branch: branchNow, dirName, ports, $, chalk };
  await config.postCreate?.(ctx);

  console.log('\n============================================');
  ok(`Worktree ready: ${wt}`);
  console.log(`Branch:         ${branchNow}`);
  const sum = config.summary?.(ctx);
  if (sum) console.log(sum);
  console.log('============================================');
}

async function dirExists(p: string): Promise<boolean> {
  try {
    await fsp.stat(p);
    return true;
  } catch {
    return false;
  }
}
