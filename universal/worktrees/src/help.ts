// Per-subcommand help text. Kept in one place so `bin/worktrees.ts` can answer
// `<sub> -h|--help` without loading config or running the command itself.

/** A flag paired with its one-line description, e.g. `['--from <base>', 'Base ref ...']`. */
type DescribedFlag = [flag: string, desc: string];

interface CommandHelp {
  /** Usage line, sans the leading "Usage: ". */
  usage: string;
  /** One- or two-line description of what the command does. */
  summary: string;
  /** Command-specific flags. `-h, --help` is appended automatically. */
  options?: DescribedFlag[];
}

const COMMANDS: Record<string, CommandHelp> = {
  setup: {
    usage: 'worktrees setup <branch> [--from <base>]',
    summary: 'Create (or refresh) a worktree for <branch>, allocate ports, and apply symlinks.',
    options: [['--from <base>', 'Base ref to branch from (default: origin/main)']],
  },
  teardown: {
    usage: 'worktrees teardown <name|branch>',
    summary:
      'Remove a worktree, clean up its port registry entry, and optionally delete the branch.',
  },
  list: {
    usage: 'worktrees list [--all]',
    summary: "List this repo's worktrees with their branch, path, and port allocations.",
    options: [['--all', 'List worktrees for every registered repo']],
  },
  sync: {
    usage: 'worktrees sync',
    summary: 'Re-apply config (reset, re-symlink, postSync) to selected worktrees (interactive).',
  },
  init: {
    usage: 'worktrees init [--in-repo]',
    summary: 'Scaffold a worktrees config for this repo and register it.',
    options: [['--in-repo', 'Print instructions for an in-repo symlinked config instead']],
  },
  'config-path': {
    usage: 'worktrees config-path',
    summary: 'Print the path to the config the engine would use for this repo.',
  },
};

/** True if `argv` requests help via `-h` or `--help`. */
export function wantsHelp(argv: string[]): boolean {
  return argv.includes('-h') || argv.includes('--help');
}

/** Formatted help text for `sub`, or null if it has no documented help. */
export function helpFor(sub: string): string | null {
  const cmd = COMMANDS[sub];
  if (!cmd) return null;

  const options: DescribedFlag[] = [...(cmd.options ?? []), ['-h, --help', 'Show this help']];
  const width = Math.max(...options.map(([flag]) => flag.length));

  const lines = [`Usage: ${cmd.usage}`, '', cmd.summary, '', 'Options:'];
  for (const [flag, desc] of options) lines.push(`  ${flag.padEnd(width)}  ${desc}`);
  return lines.join('\n');
}
