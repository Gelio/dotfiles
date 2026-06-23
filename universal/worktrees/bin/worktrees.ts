#!/usr/bin/env node

import { helpFor, wantsHelp } from '../src/help.ts';

function usage(): void {
  console.error(
    [
      'Usage: worktrees <command> [args]',
      '',
      'Commands:',
      '  setup <branch> [--from <base>]   Create/refresh a worktree for <branch>',
      '  teardown <name|branch>           Remove a worktree (interactive)',
      "  list [--all]                     List this repo's worktrees (--all: every registered repo)",
      '  sync                             Re-apply config to selected worktrees (interactive)',
      '  init                             Scaffold a config for this repo',
      "  config-path                      Print the path to this repo's config file",
    ].join('\n'),
  );
}

async function main(argv: string[]): Promise<void> {
  const [sub, ...rest] = argv;

  // `<sub> -h|--help` prints that subcommand's help and exits cleanly, before
  // any config loading or command logic runs. Unknown subcommands (helpFor ===
  // null) fall through to the switch, which reports the error via usage().
  if (sub && wantsHelp(rest)) {
    const help = helpFor(sub);
    if (help !== null) {
      console.log(help);
      return;
    }
  }

  switch (sub) {
    case 'setup':
      await (await import('../src/commands/setup.ts')).cmdSetup(rest);
      break;
    case 'teardown':
      await (await import('../src/commands/teardown.ts')).cmdTeardown(rest);
      break;
    case 'list':
      await (await import('../src/commands/list.ts')).cmdList(rest);
      break;
    case 'sync':
      await (await import('../src/commands/sync.ts')).cmdSync();
      break;
    case 'init':
      await (await import('../src/commands/init.ts')).cmdInit();
      break;
    case 'config-path':
      await (await import('../src/commands/config-path.ts')).cmdConfigPath();
      break;
    case '_config':
      await (await import('../src/config.ts')).debugConfig();
      break;
    case '__complete':
      await (await import('../src/commands/complete.ts')).cmdComplete(rest);
      break;
    case '-h':
    case '--help':
      usage();
      break;
    default:
      if (sub) console.error(`Unknown subcommand: ${sub}`);
      usage();
      process.exit(1);
  }
}

if (import.meta.main) {
  main(process.argv.slice(2)).catch((e: unknown) => {
    console.error(`Error: ${e instanceof Error ? e.message : String(e)}`);
    process.exit(1);
  });
}
