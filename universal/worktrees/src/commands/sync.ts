import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
import { $, chalk } from 'zx';
import { ask } from '../prompt.ts';
import { git, gitOk } from '../git.ts';
import { loadConfig } from '../config.ts';
import { computePorts, readPortRegistry } from '../ports.ts';
import { applySymlinks } from '../symlinks.ts';

async function dirExists(p: string): Promise<boolean> {
  try {
    await fsp.stat(p);
    return true;
  } catch {
    return false;
  }
}

export async function cmdSync(): Promise<void> {
  const { config, repo } = await loadConfig();
  const wtDir = path.join(repo, 'worktrees');

  const reg = await readPortRegistry(repo);
  let names: string[];
  if (reg.size > 0) {
    names = [...reg.keys()];
  } else {
    try {
      const ents = await fsp.readdir(wtDir, { withFileTypes: true });
      names = ents.filter((e) => e.isDirectory()).map((e) => e.name);
    } catch {
      names = [];
    }
  }

  const entries: { name: string; branch: string }[] = [];
  for (const name of names) {
    const wt = path.join(wtDir, name);
    if (!(await dirExists(wt))) continue;
    let branch = 'detached';
    try {
      branch = (await git(['branch', '--show-current'], wt)) || 'detached';
    } catch {
      /* ignore */
    }
    entries.push({ name, branch });
  }
  if (entries.length === 0) {
    console.log('No active worktrees found.');
    return;
  }

  console.log('Available worktrees:');
  entries.forEach((e, i) => console.log(`  ${i + 1}) ${e.name} (branch: ${e.branch})`));
  console.log('  a) All\n');
  const sel = (await ask('Select worktrees to sync (e.g. 1 3, or a for all): ')).trim();

  let chosen: number[] = [];
  if (/^a$/i.test(sel)) {
    chosen = entries.map((_, i) => i);
  } else {
    for (const tok of sel.split(/\s+/)) {
      const n = Number(tok);
      if (Number.isInteger(n) && n >= 1 && n <= entries.length) chosen.push(n - 1);
      else if (tok) console.error(`Invalid selection: ${tok}`);
    }
  }
  if (chosen.length === 0) {
    console.log('No worktrees selected.');
    return;
  }

  let synced = 0;
  for (const i of chosen) {
    const { name, branch } = entries[i];
    const wt = path.join(wtDir, name);
    if (await gitOk(['diff', '--diff-filter=M', '--quiet'], wt)) {
      // exit 0 = no content-modified files -> safe to reset
    } else {
      console.log(`WARNING: ${name} has unstaged changes — skipping (resolve manually)`);
      continue;
    }
    console.log(`Syncing ${name} (branch: ${branch})...`);
    await git(['reset', '--hard', 'HEAD'], wt);
    const idx = reg.get(name);
    const ports = idx !== undefined ? computePorts(config, idx) : {};
    await applySymlinks(repo, wt, config);
    await config.postSync?.({ wt, mainRepo: repo, branch, dirName: name, ports, $, chalk });
    console.log('  done');
    synced++;
  }
  console.log(`\nSynced ${synced} worktree(s).`);
}
