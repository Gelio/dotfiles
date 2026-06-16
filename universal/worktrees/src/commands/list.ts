import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
import type { ResolvedWorktreesConfig } from '../types.ts';
import { git } from '../git.ts';
import { CONFIG_HOME, loadConfig, loadConfigFor } from '../config.ts';
import { computePorts, hasPorts, readPortRegistry } from '../ports.ts';

function pad(s: string, n: number, fill = ' '): string {
  return s.padEnd(n, fill);
}

function portsString(config: ResolvedWorktreesConfig, index: number): string {
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

interface Worktree {
  /** Absolute path to the worktree's working tree. */
  path: string;
  /** Checked-out branch, or `'detached'` for a detached HEAD. */
  branch: string;
  /** git reports the worktree's dir is gone (a removed-but-unpruned worktree). */
  prunable: boolean;
}

/** Parse `git worktree list --porcelain` into one entry per worktree. */
function parseWorktrees(porcelain: string): Worktree[] {
  const entries: Worktree[] = [];
  let cur: Worktree | null = null;
  for (const line of porcelain.split('\n')) {
    if (line.startsWith('worktree ')) {
      cur = { path: line.slice('worktree '.length), branch: 'detached', prunable: false };
      entries.push(cur);
    } else if (!cur) {
      continue;
    } else if (line.startsWith('branch ')) {
      cur.branch = line.slice('branch '.length).replace(/^refs\/heads\//, '');
    } else if (line.startsWith('prunable')) {
      cur.prunable = true;
    }
  }
  return entries;
}

async function listOne(repo: string, config: ResolvedWorktreesConfig): Promise<void> {
  type Row = { branch: string; pathCol: string; ports: string };
  const rows: Row[] = [];
  const reg = await readPortRegistry(repo);

  // Enumerate from git itself rather than the port registry: this lists every
  // worktree (including port-less repos that keep no registry) and reports each
  // one's real path — which can diverge from its dir name after a `git checkout`.
  let worktrees: Worktree[] = [];
  try {
    worktrees = parseWorktrees(await git(['worktree', 'list', '--porcelain'], repo));
  } catch {
    /* not a git repo / git error — fall through to a best-effort main row */
  }
  // git always lists the main worktree first; synthesize a row if git gave us
  // nothing so the output is never empty.
  if (worktrees.length === 0) {
    let mainBranch = 'unknown';
    try {
      mainBranch = (await git(['branch', '--show-current'], repo)) || 'unknown';
    } catch {
      /* ignore */
    }
    worktrees = [{ path: repo, branch: mainBranch, prunable: false }];
  }

  for (const [i, wt] of worktrees.entries()) {
    const isMain = i === 0;
    const name = path.basename(wt.path);
    const stale = wt.prunable || !(await dirExists(wt.path));
    const status = stale ? ' [STALE]' : '';
    const rel = isMain ? '.' : `./${path.relative(repo, wt.path)}`;
    const index = isMain ? 0 : reg.get(name);
    const ports = index === undefined ? '-' : portsString(config, index);
    rows.push({
      branch: wt.branch,
      pathCol: `${rel}${status}`,
      ports: isMain ? `${ports} (main)` : ports,
    });
  }

  // Registry entries git no longer knows about (worktree removed and pruned)
  // still get a STALE row so the orphaned port index stays visible.
  const known = new Set(worktrees.map((w) => path.basename(w.path)));
  for (const [name, index] of reg) {
    if (known.has(name)) continue;
    rows.push({
      branch: '?',
      pathCol: `./worktrees/${name} [STALE]`,
      ports: portsString(config, index),
    });
  }

  const c1 = Math.max(6, ...rows.map((r) => r.branch.length)) + 2;
  const c2 = Math.max(4, ...rows.map((r) => r.pathCol.length)) + 2;
  const c3 = Math.max(5, ...rows.map((r) => r.ports.length)) + 2;
  console.log(pad('BRANCH', c1) + pad('PATH', c2) + pad('PORTS', c3));
  console.log(pad('', c1, '-') + pad('', c2, '-') + pad('', c3, '-'));
  for (const r of rows) console.log(pad(r.branch, c1) + pad(r.pathCol, c2) + pad(r.ports, c3));
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
