import { spawnSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ENGINE = path.join(HERE, '..', 'bin', 'worktrees.ts');

export function makeRepo(dir: string): string {
  fs.mkdirSync(dir, { recursive: true });
  const g = (...a: string[]) => spawnSync('git', ['-C', dir, ...a], { encoding: 'utf8' });
  g('init', '-q', '-b', 'main');
  g('config', 'user.email', 't@t.t');
  g('config', 'user.name', 'test');
  fs.writeFileSync(path.join(dir, 'README.md'), 'root\n');
  g('add', '-A');
  g('commit', '-qm', 'init');
  return dir;
}

export function sandbox(): { root: string; repo: string; configHome: string } {
  // Use realpathSync so the returned paths are canonical (e.g., /private/tmp
  // rather than /tmp on macOS), matching what git and process.cwd() return.
  const root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'wt-')));
  const repo = makeRepo(path.join(root, 'repo'));
  const configHome = path.join(root, 'config');
  return { root, repo, configHome };
}

export function runEngine(
  cwd: string,
  args: string[],
  opts: { input?: string; configHome?: string } = {},
): { out: string; code: number } {
  const res = spawnSync('node', ['--experimental-strip-types', ENGINE, ...args], {
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
