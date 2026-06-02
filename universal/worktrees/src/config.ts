import * as fs from 'node:fs';
import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
import * as os from 'node:os';
import { pathToFileURL } from 'node:url';
import type { WorktreesConfig } from './types.ts';
import { die } from './log.ts';
import { repoRoot } from './git.ts';

export const CONFIG_HOME =
  process.env.WORKTREES_CONFIG_HOME && process.env.WORKTREES_CONFIG_HOME.length > 0
    ? process.env.WORKTREES_CONFIG_HOME
    : path.join(os.homedir(), '.config', 'worktrees');

const CONFIG_EXTS = ['.mts', '.ts'] as const;

/** Sanitized key for a repo's absolute toplevel: /a/b/c -> a-b-c */
export function repoKey(repo: string): string {
  return repo.replace(/^\//, '').replace(/\//g, '-');
}

function isLink(p: string): boolean {
  try {
    return fs.lstatSync(p).isSymbolicLink();
  } catch {
    return false;
  }
}

/**
 * True iff `configPath` is a symlink whose realpath resolves OUTSIDE `repo`.
 * Refuses plain files and symlinks pointing back inside the repo (RCE vectors,
 * since the engine imports the resolved module).
 */
export function configPathIsSafe(repo: string, configPath: string): boolean {
  let st: fs.Stats;
  try {
    st = fs.lstatSync(configPath);
  } catch {
    return false;
  }
  if (!st.isSymbolicLink()) return false;
  let target: string;
  let repoReal: string;
  try {
    target = fs.realpathSync(configPath);
    repoReal = fs.realpathSync(repo);
  } catch {
    return false;
  }
  const rel = path.relative(repoReal, target);
  const inside = rel === '' || (!rel.startsWith('..') && !path.isAbsolute(rel));
  return !inside;
}

function resolveConfigSource(repo: string): string | null {
  for (const ext of CONFIG_EXTS) {
    const f = path.join(repo, `.worktrees${ext}`);
    if ((fs.existsSync(f) || isLink(f)) && configPathIsSafe(repo, f)) return f;
  }
  for (const ext of CONFIG_EXTS) {
    const c = path.join(CONFIG_HOME, 'repos', `${repoKey(repo)}${ext}`);
    if (fs.existsSync(c)) return c;
  }
  return null;
}

/** Append `<repo>\t<source>` to the registry, exactly one line per repo. */
export async function registerRepo(repo: string, source: string): Promise<void> {
  await fsp.mkdir(CONFIG_HOME, { recursive: true });
  const reg = path.join(CONFIG_HOME, 'registry');
  let lines: string[] = [];
  try {
    lines = (await fsp.readFile(reg, 'utf8')).split('\n').filter(Boolean);
  } catch {
    /* none yet */
  }
  const kept = lines.filter((l) => l.split('\t')[0] !== repo);
  kept.push(`${repo}\t${source}`);
  await fsp.writeFile(reg, kept.join('\n') + '\n');
}

export interface LoadedConfig {
  source: string;
  config: WorktreesConfig;
  repo: string;
}

/** Resolve the repo, discover + import its config, register it. */
export async function loadConfig(): Promise<LoadedConfig> {
  const repo = await repoRoot();
  const source = resolveConfigSource(repo);
  if (!source) die(`no worktrees config for ${repo} — run: worktrees init`);
  const mod = (await import(pathToFileURL(source).href)) as {
    default?: WorktreesConfig;
  } & WorktreesConfig;
  const config: WorktreesConfig = mod.default ?? mod;
  await registerRepo(repo, source);
  return { source, config, repo };
}

/** Load a config for an explicit repo path (used by `list --all`). */
export async function loadConfigFor(repo: string): Promise<WorktreesConfig> {
  const source = resolveConfigSource(repo);
  if (!source) throw new Error(`no worktrees config for ${repo}`);
  const mod = (await import(pathToFileURL(source).href)) as {
    default?: WorktreesConfig;
  } & WorktreesConfig;
  return mod.default ?? mod;
}

/** Test-only debug arm wired into the entry. */
export async function debugConfig(): Promise<void> {
  const { source } = await loadConfig();
  console.log(`config: ${source}`);
}
