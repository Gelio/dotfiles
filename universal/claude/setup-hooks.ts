#!/usr/bin/env node
// Merge hooks.json into ~/.claude/settings.json
//
// Usage:
//   node --experimental-strip-types setup-hooks.ts
//
// This reads hooks from hooks.json (adjacent to this script) and deep-merges
// them into ~/.claude/settings.json, preserving all other settings and
// existing hook entries. For each event type (e.g. "Stop"), new matcher
// entries are appended if they don't already exist (matched by command string).
// Requires: Node.js 24+ (with native type-stripping).

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";

interface HookCommand {
  type: string;
  command: string;
}

interface HookMatcher {
  matcher: string;
  hooks: HookCommand[];
}

type HooksConfig = Record<string, HookMatcher[]>;

const scriptDir: string = dirname(fileURLToPath(import.meta.url));
const settingsPath: string = join(homedir(), ".claude", "settings.json");
const hooksPath: string = join(scriptDir, "hooks.json");

if (!existsSync(hooksPath)) {
  console.error(`Error: ${hooksPath} not found.`);
  process.exit(1);
}

const settings: Record<string, unknown> = existsSync(settingsPath)
  ? JSON.parse(readFileSync(settingsPath, "utf-8"))
  : {};

const hooksFile: { hooks: HooksConfig } = JSON.parse(
  readFileSync(hooksPath, "utf-8"),
);

const existingHooks: HooksConfig = (settings.hooks as HooksConfig) ?? {};

// Deep-merge: for each event type, append matcher entries whose commands
// are not already present.
for (const [eventType, newMatchers] of Object.entries(hooksFile.hooks)) {
  const existing: HookMatcher[] = existingHooks[eventType] ?? [];

  for (const newMatcher of newMatchers) {
    // Check if an entry with the same matcher pattern already contains
    // the same hook commands.
    const matchingEntry = existing.find(
      (e) => e.matcher === newMatcher.matcher,
    );

    if (matchingEntry) {
      // Append only hook commands that don't already exist
      for (const newHook of newMatcher.hooks) {
        const alreadyExists = matchingEntry.hooks.some(
          (h) => h.type === newHook.type && h.command === newHook.command,
        );
        if (!alreadyExists) {
          matchingEntry.hooks.push(newHook);
        }
      }
    } else {
      existing.push(newMatcher);
    }
  }

  existingHooks[eventType] = existing;
}

settings.hooks = existingHooks;

writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + "\n");
console.log(`Hooks merged into ${settingsPath}`);
