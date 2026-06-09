import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
import * as os from 'node:os';
import { repoRoot } from '../git.ts';
import { CONFIG_HOME, registerRepo, repoKey } from '../config.ts';

// Stable type-import path: via the project dir symlink created by install.sh.
const TYPES_PATH = path.join(os.homedir(), '.local', 'share', 'worktrees', 'src', 'types.ts');

function scaffold(): string {
  return `import type { WorktreesConfig } from ${JSON.stringify(TYPES_PATH)};

const config: WorktreesConfig = {
  // Named base ports. Engine computes base + index*step per worktree and
  // passes them to hooks as ctx.ports. Omit entirely if no ports are needed.
  // ports: { UI_DEV: 3003, SERVER: 3004 },
  portStep: 10,

  // Files/dirs symlinked from the main repo into each worktree.
  symlinkTargets: ['CLAUDE.md', 'AGENTS.md', 'agent-docs', 'agent-plans'],

  // Dirs merge-symlinked recursively (tracked files preserved; e.g. .claude).
  mergeSymlinkDirs: ['.claude'],

  // After the worktree exists, ports computed, symlinks applied.
  async postCreate({ wt, ports }) {
    // const { writeFile } = await import('node:fs/promises');
    // await writeFile(\`\${wt}/.env\`, \`PORT=\${ports.UI_DEV}\\n\`);
  },

  // Re-applied during \`sync\` after reset + re-symlink.
  async postSync({ wt }) {},

  // Optional footer string printed at the end of \`setup\`.
  summary({ ports }) {
    return '';
  },
};

export default config;
`;
}

async function excludeAdd(repo: string, pattern: string): Promise<void> {
  const ex = path.join(repo, '.git', 'info', 'exclude');
  await fsp.mkdir(path.dirname(ex), { recursive: true });
  let lines: string[] = [];
  try {
    lines = (await fsp.readFile(ex, 'utf8')).split('\n');
  } catch {
    /* none */
  }
  if (!lines.includes(pattern)) {
    // Drop only the trailing empty element from a final newline (not internal
    // blank lines) so the re-joined file keeps exactly one trailing newline.
    const trimmed = lines.filter((l, i) => !(l === '' && i === lines.length - 1));
    trimmed.push(pattern);
    await fsp.writeFile(ex, trimmed.join('\n') + '\n');
  }
}

async function fileExists(p: string): Promise<boolean> {
  try {
    await fsp.stat(p);
    return true;
  } catch {
    return false;
  }
}

export async function cmdInit(argv: string[]): Promise<void> {
  const repo = await repoRoot();

  if (argv[0] === '--in-repo') {
    await excludeAdd(repo, '.worktrees.mts');
    await excludeAdd(repo, '.worktrees.ts');
    const baseName = path.basename(repo);
    console.log('In-repo config selected. Create the config in your dotfiles and symlink it:\n');
    console.log(
      `  ln -s "$PWD/path/to/dotfiles/${baseName}/.worktrees.mts" "${repo}/.worktrees.mts"\n`,
    );
    console.log(
      `The engine imports <repo>/.worktrees.{mts,ts} ONLY when it is a symlink whose target ` +
        `resolves OUTSIDE the repo (security guard). Added '.worktrees.mts' and '.worktrees.ts' ` +
        `to ${repo}/.git/info/exclude (idempotent).\n`,
    );
    console.log('Starter config to copy:');
    console.log('------------------------------------------------------------');
    console.log(scaffold());
    return;
  }

  const dest = path.join(CONFIG_HOME, 'repos', `${repoKey(repo)}.mts`);
  if (await fileExists(dest)) {
    console.log(`Config already exists: ${dest} (leaving it untouched)`);
  } else {
    await fsp.mkdir(path.dirname(dest), { recursive: true });
    await fsp.writeFile(dest, scaffold());
    console.log(`Scaffolded config: ${dest}`);
  }
  await registerRepo(repo, dest);
  console.log(`Registered ${repo}. Edit the config, then run: worktrees setup <branch>`);
}
