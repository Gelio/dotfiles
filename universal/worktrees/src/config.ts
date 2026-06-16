import * as fs from 'node:fs';
import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
import * as os from 'node:os';
import { pathToFileURL } from 'node:url';
import type { WorktreesConfig, ResolvedWorktreesConfig } from './types.ts';
import { die } from './log.ts';
import { repoRoot } from './git.ts';

export const CONFIG_HOME =
  process.env.WORKTREES_CONFIG_HOME && process.env.WORKTREES_CONFIG_HOME.length > 0
    ? process.env.WORKTREES_CONFIG_HOME
    : path.join(os.homedir(), '.config', 'worktrees');

export const CONFIG_EXTS = ['.mts', '.ts', '.mjs', '.js'] as const;

const DEFAULT_PORT_STEP = 10;
/** Apply engine defaults to a raw config. */
export function resolveConfig(config: WorktreesConfig): ResolvedWorktreesConfig {
  return { ...config, portStep: config.portStep ?? DEFAULT_PORT_STEP };
}

/** Sanitized key for a repo's absolute toplevel: /a/b/c -> a-b-c */
export function repoKey(repo: string): string {
  return repo.replace(/^\//, '').replace(/\//g, '-');
}

/** Central config dir for a config home: `<configHome>/repos`. */
export function reposDir(configHome: string): string {
  return path.join(configHome, 'repos');
}
/** Central config path for a repo: `<configHome>/repos/<repoKey>.<ext>`. */
export function centralConfigPath(configHome: string, repo: string, ext = '.mts'): string {
  return path.join(reposDir(configHome), `${repoKey(repo)}${ext}`);
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

export function resolveConfigSource(repo: string): string | null {
  for (const ext of CONFIG_EXTS) {
    const f = path.join(repo, `.worktrees${ext}`);
    if ((fs.existsSync(f) || isLink(f)) && configPathIsSafe(repo, f)) return f;
  }
  for (const ext of CONFIG_EXTS) {
    const c = centralConfigPath(CONFIG_HOME, repo, ext);
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
  config: ResolvedWorktreesConfig;
  repo: string;
}

/**
 * Dynamically import a resolved config module and unwrap it.
 * `export default` configs arrive as `mod.default` (the normal path); the
 * `?? mod` fallback supports a config authored as named/namespace exports
 * without a default export.
 */
async function importConfig(source: string): Promise<ResolvedWorktreesConfig> {
  // The dynamic import of an arbitrary user config module is `any`; asserting
  // the expected shape here is intentional (it is validated by resolveConfig).
  // oxlint-disable-next-line typescript/no-unsafe-type-assertion
  const mod = (await import(pathToFileURL(source).href)) as {
    default?: WorktreesConfig;
  } & WorktreesConfig;
  return resolveConfig(mod.default ?? mod);
}

/** Resolve the repo, discover + import its config, register it. */
export async function loadConfig(): Promise<LoadedConfig> {
  const repo = await repoRoot();
  const source = resolveConfigSource(repo);
  if (!source) die(`no worktrees config for ${repo} — run: worktrees init`);
  const config = await importConfig(source);
  await registerRepo(repo, source);
  return { source, config, repo };
}

/** Load a config for an explicit repo path (used by `list --all`). */
export async function loadConfigFor(repo: string): Promise<ResolvedWorktreesConfig> {
  const source = resolveConfigSource(repo);
  if (!source) throw new Error(`no worktrees config for ${repo}`);
  return importConfig(source);
}

/** Test-only debug arm wired into the entry. */
export async function debugConfig(): Promise<void> {
  const { source } = await loadConfig();
  console.log(`config: ${source}`);
}
