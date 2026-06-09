import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
import type { WorktreesConfig } from '../types.ts';
import { git } from '../git.ts';
import { CONFIG_HOME, loadConfig, loadConfigFor } from '../config.ts';
import { computePorts, hasPorts, readPortRegistry } from '../ports.ts';

function portsString(config: WorktreesConfig, index: number): string {
  if (!hasPorts(config)) return '-';
  return Object.values(computePorts(config, index)).join('/');
}

async function dirExists(p: string): Promise<boolean> {
  try {
    await fsp.stat(p);
    return true;
  } catch {
    return false;
  }
}

async function listOne(repo: string, config: WorktreesConfig): Promise<void> {
  type Row = { branch: string; pathCol: string; ports: string };
  const rows: Row[] = [];

  let mainBranch = 'unknown';
  try {
    mainBranch = (await git(['branch', '--show-current'], repo)) || 'unknown';
  } catch {
    /* ignore */
  }
  rows.push({ branch: mainBranch, pathCol: '.', ports: `${portsString(config, 0)} (main)` });

  for (const [name, index] of await readPortRegistry(repo)) {
    const wt = path.join(repo, 'worktrees', name);
    let branch = '?';
    let status = '';
    if (await dirExists(wt)) {
      try {
        branch = (await git(['branch', '--show-current'], wt)) || '?';
      } catch {
        /* ignore */
      }
    } else {
      status = ' [STALE]';
    }
    rows.push({
      branch,
      pathCol: `./worktrees/${name}${status}`,
      ports: portsString(config, index),
    });
  }

  const c1 = Math.max(6, ...rows.map((r) => r.branch.length)) + 2;
  const c2 = Math.max(4, ...rows.map((r) => r.pathCol.length)) + 2;
  const pad = (s: string, n: number) => s.padEnd(n);
  console.log(pad('BRANCH', c1) + pad('PATH', c2) + 'PORTS');
  console.log(pad('------', c1) + pad('----', c2) + '-----');
  for (const r of rows) console.log(pad(r.branch, c1) + pad(r.pathCol, c2) + r.ports);
}

export async function cmdList(argv: string[]): Promise<void> {
  if (argv[0] === '--all') {
    const reg = path.join(CONFIG_HOME, 'registry');
    let text: string;
    try {
      text = await fsp.readFile(reg, 'utf8');
    } catch {
      console.log('No repos registered.');
      return;
    }
    for (const line of text.split('\n').filter(Boolean)) {
      const repo = line.split('\t')[0];
      if (!(await dirExists(repo))) continue;
      console.log(`### ${repo}`);
      try {
        await listOne(repo, await loadConfigFor(repo));
      } catch (e) {
        console.log(`  (config error: ${e instanceof Error ? e.message : String(e)})`);
      }
      console.log('');
    }
    return;
  }
  const { config, repo } = await loadConfig();
  await listOne(repo, config);
}
