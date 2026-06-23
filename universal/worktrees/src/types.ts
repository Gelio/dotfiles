/** Context passed to every config hook. */
export interface HookContext {
  /** Absolute path to the worktree. */
  wt: string;
  /** Absolute path to the main repo toplevel. */
  mainRepo: string;
  /** The worktree's current branch. */
  branch: string;
  /** Sanitized directory name (branch with `/` -> `-`). */
  dirName: string;
  /** Computed ports for this worktree: name -> base + index*step. */
  ports: Record<string, number>;
  /**
   * zx's `$`, injected by the engine. Configs use this instead of
   * `import`ing zx — a dynamically-imported config resolves its own imports
   * relative to ITS location (the repo's dotfiles), where zx is NOT installed.
   * Injection sidesteps that and gives configs zx ergonomics for free.
   */
  $: (typeof import('zx'))['$'];
  /** zx's chalk, for colored hook output. */
  chalk: (typeof import('zx'))['chalk'];
}

/** A repo's worktrees config — `export default` this from the central config. */
export interface WorktreesConfig {
  /** Named base ports. Omit entirely if the repo needs no ports. */
  ports?: Record<string, number>;
  /** Port spacing between worktree indices. Default 10. */
  portStep?: number;
  /** Files/dirs symlinked from the main repo into each worktree. */
  symlinkTargets?: string[];
  /** Dirs merge-symlinked recursively (tracked files preserved). */
  mergeSymlinkDirs?: string[];
  /** After worktree exists, ports computed, symlinks applied. */
  postCreate?(ctx: HookContext): void | Promise<void>;
  /** Re-applied per selected worktree during `sync`, after reset + re-symlink. */
  postSync?(ctx: HookContext): void | Promise<void>;
  /** Optional footer string printed at the end of `setup`. */
  summary?(ctx: HookContext): string | void;
}

/** A WorktreesConfig with engine defaults applied (portStep guaranteed). */
export interface ResolvedWorktreesConfig extends WorktreesConfig {
  portStep: number;
}
