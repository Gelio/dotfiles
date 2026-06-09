import { spawnSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';
import { fileURLToPath } from 'node:url';
import type { TestContext } from 'node:test';
import { reposDir, centralConfigPath } from '../src/config.ts';

// The Node v24 runtime exposes `TestContext#passed` (a boolean, readable from
// `t.after` hooks), but @types/node (both ^22 and ^24 as of writing) does not
// type it on TestContext. Augment it locally rather than bumping the dependency,
// since the bump would not add the property anyway.
declare module 'node:test' {
  interface TestContext {
    readonly passed: boolean;
  }
}

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ENGINE = path.join(HERE, '..', 'bin', 'worktrees.ts');

export function makeRepo(dir: string): string {
  fs.mkdirSync(dir, { recursive: true });
  const g = (...a: string[]) => spawnSync('git', ['-C', dir, ...a], { encoding: 'utf8' });
  g('init', '-q', '-b', 'main');
  g('config', 'user.email', 't@t.t');
  g('config', 'user.name', 'test');
  g('config', 'commit.gpgsign', 'false');
  fs.writeFileSync(path.join(dir, 'README.md'), 'root\n');
  g('add', '-A');
  g('commit', '-qm', 'init');
  g('update-ref', 'refs/remotes/origin/main', 'HEAD');
  return dir;
}

export function sandbox(t: TestContext): { root: string; repo: string; configHome: string } {
  // Use realpathSync so the returned paths are canonical (e.g., /private/tmp
  // rather than /tmp on macOS), matching what git and process.cwd() return.
  const root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'wt-')));
  t.diagnostic(`sandbox: ${root}`);
  t.after(() => {
    // Clean up only on success; keep the dir on failure so it can be inspected.
    if (t.passed) fs.rmSync(root, { recursive: true, force: true });
    else t.diagnostic(`kept sandbox for debugging: ${root}`);
  });
  const repo = makeRepo(path.join(root, 'repo'));
  const configHome = path.join(root, 'config');
  return { root, repo, configHome };
}

export function runEngine(
  cwd: string,
  args: string[],
  opts: { input?: string; configHome?: string } = {},
): { out: string; code: number } {
  const res = spawnSync('node', [ENGINE, ...args], {
    cwd,
    input: opts.input ?? '',
    encoding: 'utf8',
    env: { ...process.env, WORKTREES_CONFIG_HOME: opts.configHome ?? '' },
  });
  return { out: (res.stdout ?? '') + (res.stderr ?? ''), code: res.status ?? 1 };
}

/** Write a config file and symlink it into the repo as a safe (outside) config. */
export function linkCfg(root: string, repo: string, body: string, name = '.worktrees.mts'): void {
  fs.writeFileSync(path.join(root, 'cfg.mts'), body);
  fs.symlinkSync(path.join(root, 'cfg.mts'), path.join(repo, name));
}

/** Write a central config at <configHome>/repos/<repoKey>.<ext>; returns its path. */
export function writeCentralConfig(
  configHome: string,
  repo: string,
  body: string,
  ext = '.mts',
): string {
  fs.mkdirSync(reposDir(configHome), { recursive: true });
  const file = centralConfigPath(configHome, repo, ext);
  fs.writeFileSync(file, body);
  return file;
}
