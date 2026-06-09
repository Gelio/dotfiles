import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
import type { Stats } from 'node:fs';
import type { WorktreesConfig } from './types.ts';
import { warn } from './log.ts';
import { git } from './git.ts';

async function lstatOrNull(p: string): Promise<Stats | null> {
  try {
    return await fsp.lstat(p);
  } catch {
    return null;
  }
}

async function exists(p: string): Promise<boolean> {
  return (await lstatOrNull(p)) !== null;
}

/**
 * Recursively merge-symlink srcDir into dstDir:
 *  - dst missing or a symlink  -> (re)symlink the whole src item
 *  - dst is a real directory   -> recurse (preserve tracked files within)
 *  - dst is a real file        -> leave alone, record in `skipped`
 */
export async function mergeSymlink(
  srcDir: string,
  dstDir: string,
  skipped: string[],
): Promise<void> {
  await fsp.mkdir(dstDir, { recursive: true });
  for (const name of await fsp.readdir(srcDir)) {
    const srcItem = path.join(srcDir, name);
    const dstItem = path.join(dstDir, name);
    const dl = await lstatOrNull(dstItem);
    if (dl?.isSymbolicLink()) {
      await fsp.rm(dstItem);
      await fsp.symlink(srcItem, dstItem);
    } else if (dl?.isDirectory()) {
      await mergeSymlink(srcItem, dstItem, skipped);
    } else if (dl) {
      skipped.push(dstItem);
    } else {
      await fsp.symlink(srcItem, dstItem);
    }
  }
}

/** (Re)create all configured symlinks into a worktree. Used by setup and sync. */
export async function applySymlinks(
  repo: string,
  wt: string,
  config: WorktreesConfig,
): Promise<void> {
  for (const target of config.symlinkTargets ?? []) {
    const src = path.join(repo, target);
    const dst = path.join(wt, target);
    if (await lstatOrNull(dst)) await fsp.rm(dst, { recursive: true, force: true });
    if (await exists(src)) {
      await fsp.mkdir(path.dirname(dst), { recursive: true });
      await fsp.symlink(src, dst);
    } else {
      warn(`Warning: ${src} does not exist, skipping symlink for ${target}`);
    }
  }
  for (const dir of config.mergeSymlinkDirs ?? []) {
    const srcDir = path.join(repo, dir);
    if (!(await exists(srcDir))) continue;
    const skipped: string[] = [];
    await mergeSymlink(srcDir, path.join(wt, dir), skipped);
    if (skipped.length) {
      console.log(`Tracked ${dir} files (not symlinked):`);
      for (const s of skipped) console.log(`  ${s}`);
    }
  }
}

/** Symlink the worktree's .git/info/exclude to the main repo's. */
export async function symlinkInfoExclude(repo: string, wt: string): Promise<void> {
  let gitDir = await git(['rev-parse', '--git-dir'], wt);
  if (!path.isAbsolute(gitDir)) gitDir = path.join(wt, gitDir);
  const wtExclude = path.join(gitDir, 'info', 'exclude');
  const mainExclude = path.join(repo, '.git', 'info', 'exclude');
  await fsp.mkdir(path.dirname(wtExclude), { recursive: true });
  if (await lstatOrNull(wtExclude)) await fsp.rm(wtExclude, { force: true });
  await fsp.symlink(mainExclude, wtExclude);
}
