import * as fsp from 'node:fs/promises';
import * as path from 'node:path';
import * as os from 'node:os';
import { repoRoot } from '../git.ts';
import { CONFIG_HOME, registerRepo, reposDir, centralConfigPath } from '../config.ts';

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

async function fileExists(p: string): Promise<boolean> {
  try {
    await fsp.stat(p);
    return true;
  } catch {
    return false;
  }
}

export async function cmdInit(): Promise<void> {
  const repo = await repoRoot();

  const dest = centralConfigPath(CONFIG_HOME, repo, '.mts');
  if (await fileExists(dest)) {
    console.log(`Config already exists: ${dest} (leaving it untouched)`);
  } else {
    await fsp.mkdir(reposDir(CONFIG_HOME), { recursive: true });
    await fsp.writeFile(dest, scaffold());
    console.log(`Scaffolded config: ${dest}`);
  }
  await registerRepo(repo, dest);
  console.log(`Registered ${repo}. Edit the config, then run: worktrees setup <branch>`);
}
