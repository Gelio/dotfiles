import { $ } from 'zx';
import { die } from './log.ts';

$.verbose = false;

/** Run git, returning trimmed stdout. Throws on non-zero exit. */
export async function git(args: string[], cwd?: string): Promise<string> {
  const out = await (cwd ? $({ cwd })`git ${args}` : $`git ${args}`);
  return out.stdout.trim();
}

/** Run git for its exit status only; true on success (exit 0). */
export async function gitOk(args: string[], cwd?: string): Promise<boolean> {
  const p = cwd ? $({ cwd })`git ${args}`.nothrow() : $`git ${args}`.nothrow();
  return (await p).exitCode === 0;
}

/** Absolute toplevel of the repo containing the cwd. Exits with a message if none. */
export async function repoRoot(): Promise<string> {
  try {
    return await git(['rev-parse', '--show-toplevel']);
  } catch {
    return die('not inside a git repo');
  }
}
