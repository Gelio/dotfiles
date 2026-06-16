import { repoRoot } from '../git.ts';
import { resolveConfigSource } from '../config.ts';
import { die } from '../log.ts';

/**
 * Print the path of the config the engine would use for this repo — a safe
 * local `.worktrees.*` symlink, else the central `<configHome>/repos/...` file.
 * Resolves the path only: it neither imports/executes the config nor registers
 * the repo, so it stays read-only and works even when the config has errors.
 */
export async function cmdConfigPath(): Promise<void> {
  const repo = await repoRoot();
  const source = resolveConfigSource(repo);
  if (!source) die(`no worktrees config for ${repo} — run: worktrees init`);
  console.log(source);
}
