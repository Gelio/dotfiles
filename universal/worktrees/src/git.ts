import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
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

/** Append a pattern to the repo's .git/info/exclude, idempotently. */
export async function addRepoExclude(repo: string, pattern: string): Promise<void> {
  const ex = path.join(repo, '.git', 'info', 'exclude');
  await fsp.mkdir(path.dirname(ex), { recursive: true });
  let lines: string[] = [];
  try {
    lines = (await fsp.readFile(ex, 'utf8')).split('\n');
  } catch {
    /* none */
  }
  if (lines.includes(pattern)) return;
  // Drop only the trailing empty element from a final newline (not internal
  // blank lines) so the re-joined file keeps exactly one trailing newline.
  const trimmed = lines.filter((l, i) => !(l === '' && i === lines.length - 1));
  trimmed.push(pattern);
  await fsp.writeFile(ex, trimmed.join('\n') + '\n');
}
