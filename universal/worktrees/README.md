# worktrees

A machine-wide `worktrees` CLI for managing parallel git worktrees with
per-repo typed configuration. Each repo describes its ports, symlinks, and
setup hooks in a single TS config file; the engine handles worktree creation,
port allocation, and hook execution.

---

## Runtime model

- **No build step.** The entry point is a TypeScript file with a
  `#!/usr/bin/env node` shebang. Node strips the types at load time; no
  compilation is needed.
- **Node ≥ 24** is required (enforced via the `engines` field in
  `package.json`). On Node 24 type-stripping is enabled by default, so no
  `--experimental-strip-types` flag is needed, and `import.meta.main` is
  available.
- If a repo pins an older Node via mise, use the escape hatch:
  ```
  mise x node@lts -- worktrees <command>
  ```
- The single runtime dependency is `zx` (installed by `install.sh`).

---

## Install

```bash
cd universal/worktrees
./install.sh
```

`install.sh` does four things:

1. Runs `npm ci` (or `npm install` when no lockfile is present) to install `zx`.
2. Creates `~/.local/share/worktrees` → this project directory (stable anchor;
   re-run install after relocating your dotfiles checkout).
3. Creates `~/.local/bin/worktrees` → `bin/worktrees.ts` (the command).
4. Symlinks shell completions: `~/.zfunc/_worktrees` (zsh) and
   `~/.local/share/bash-completion/completions/worktrees` (bash).

Ensure `~/.local/bin` is on your `$PATH`.

---

## Shell completions

`install.sh` installs zsh and bash completions for subcommands, flags, and
two dynamic value slots: `setup --from <ref>` (local + remote branches) and
`teardown <name>` (existing worktree dir names).

They are *hybrid*: subcommands and flags complete in-shell (no Node startup);
only the dynamic slots shell out to a hidden `worktrees __complete` subcommand,
which is the single source of truth for those candidates and stays silent
(exit 0, no output) outside a git repo.

- **zsh** — `~/.zfunc` is assumed to be on `$fpath` with `compinit` loaded
  (this repo's `.zshrc` does both). Start a new shell after install.
- **bash** — requires the `bash-completion` package; the file lands in its
  standard per-command autoload dir.

---

## Commands

| Command | What it does |
|---|---|
| `worktrees init` | Scaffold a central config for the current repo at `~/.config/worktrees/repos/<repo-key>.mts`. |
| `worktrees init --in-repo` | Print a starter config and add `.worktrees.{mts,ts,mjs,js}` to `.git/info/exclude`. Use when you want the config symlinked from a dotfiles checkout into the repo root. |
| `worktrees setup <branch> [--from <base>]` | Create (or refresh) a worktree at `worktrees/<dir>/` for `<branch>`, branching from `<base>` (default: `origin/main`). Allocates ports, applies symlinks, runs `postCreate`. |
| `worktrees teardown <name\|branch>` | Interactively remove a worktree, clean up the port registry, and optionally delete the branch. |
| `worktrees list` | List worktrees for the current repo with branch, path, and port allocations. Marks stale entries. |
| `worktrees list --all` | List worktrees for every repo in the central registry. |
| `worktrees sync` | Interactively re-apply config (reset, re-symlink, `postSync`) to selected worktrees. |
| `worktrees config-path` | Print the path to the config the engine would use for the current repo (the local symlink or the central file, per the discovery order below). Resolves the path only — it does not import/execute the config — so it works even with a broken config. Exits non-zero if no config exists. |

---

## Config discovery and security guard

For the repo rooted at `$CWD`, the engine resolves config in this order:

1. **`<repo>/.worktrees.{mts,ts,mjs,js}`** (TS variants take precedence) —
   accepted **only** when it is a symlink whose `realpath` resolves **outside**
   the repo. Plain files and symlinks pointing back inside the repo are refused
   as RCE vectors (the engine `import()`s the resolved module).
2. **`~/.config/worktrees/repos/<repo-key>.{mts,ts,mjs,js}`** — central
   fallback, always accepted (plain files are fine here).

Override the config home with `WORKTREES_CONFIG_HOME`:

```bash
WORKTREES_CONFIG_HOME=/path/to/configs worktrees list
```

A de-duplicated registry at `~/.config/worktrees/registry` (TSV
`<repo>\t<source>`) is updated automatically on every command that loads a
config and is read by `list --all`.

---

## WorktreesConfig contract

Repo configs are `.mts` files (or `.ts` in a `"type":"module"` repo). Plain
JavaScript is also accepted — `.mjs`, or `.js` in a `"type":"module"` repo —
for users who don't want TypeScript (no type-checking, but the
`WorktreesConfig` shape still applies). They `export default` a
`WorktreesConfig` object.

Import types from the stable path created by `install.sh`:

```ts
import type { WorktreesConfig } from '~/.local/share/worktrees/src/types.ts';
```

> **Important:** configs must import **only** `node:*` builtins — not `zx` or
> any other package. The engine injects `ctx.$` and `ctx.chalk` so hooks get
> zx ergonomics without needing zx installed in the repo's `node_modules`.
> (A dynamically-imported config resolves its own imports relative to its
> `realpath`, where zx is not present.)

### Declaration fields

| Field | Type | Default | Description |
|---|---|---|---|
| `ports` | `Record<string, number>` | — | Named base ports. Omit entirely if the repo needs no ports. |
| `portStep` | `number` | `10` | Port spacing between worktree indices. |
| `symlinkTargets` | `string[]` | — | Files/dirs symlinked from the main repo into each worktree. A target that git **tracks** is left as the worktree's own checkout (symlinking over it would show as a dirty `typechange`); untracked targets are symlinked and added to the repo's `.git/info/exclude` so the link never pollutes `git status`. |
| `mergeSymlinkDirs` | `string[]` | — | Dirs that are merge-symlinked recursively: each entry inside the dir is symlinked individually, preserving any tracked files in the worktree. |

### Hooks

All hooks receive a `HookContext` and may return `void` or a `Promise<void>`.

| Hook | When it runs |
|---|---|
| `postCreate(ctx)` | After the worktree exists, ports are computed, and symlinks are applied. |
| `postSync(ctx)` | Per selected worktree during `sync`, after reset and re-symlink. |
| `summary(ctx): string \| void` | Optional; the returned string is printed at the end of `setup`. |

### HookContext fields

| Field | Type | Description |
|---|---|---|
| `wt` | `string` | Absolute path to the worktree. |
| `mainRepo` | `string` | Absolute path to the main repo root. |
| `branch` | `string` | The worktree's current branch. |
| `dirName` | `string` | Sanitized directory name (`branch` with `/` → `-`). |
| `ports` | `Record<string, number>` | Computed ports: `base + index * portStep` for each named port. |
| `$` | zx `$` | Injected by the engine. Use for shell commands in hooks. |
| `chalk` | zx `chalk` | Injected by the engine. Use for colored output in hooks. |

---

## Example config

```ts
// ~/.config/worktrees/repos/home-my-project.mts
// (or symlinked from dotfiles to <repo>/.worktrees.mts)

import type { WorktreesConfig } from '~/.local/share/worktrees/src/types.ts';

const config: WorktreesConfig = {
  // Named base ports. Each worktree gets base + index * portStep.
  ports: {
    UI_DEV: 3003,
    SERVER: 3004,
  },
  portStep: 10,

  // Symlink these from the main repo into every worktree.
  symlinkTargets: ['CLAUDE.md', 'agent-docs', 'agent-plans'],

  // Merge-symlink .claude: individual entries are linked, tracked files preserved.
  mergeSymlinkDirs: ['.claude'],

  // Write a .env after the worktree is ready.
  async postCreate({ wt, ports }) {
    const { writeFile } = await import('node:fs/promises');
    await writeFile(
      `${wt}/.env`,
      `UI_DEV_PORT=${ports.UI_DEV}\nSERVER_PORT=${ports.SERVER}\n`,
    );
  },

  // Re-apply .env on sync too.
  async postSync({ wt, ports }) {
    const { writeFile } = await import('node:fs/promises');
    await writeFile(
      `${wt}/.env`,
      `UI_DEV_PORT=${ports.UI_DEV}\nSERVER_PORT=${ports.SERVER}\n`,
    );
  },

  summary({ ports }) {
    return `UI: http://localhost:${ports.UI_DEV}  Server: http://localhost:${ports.SERVER}`;
  },
};

export default config;
```
