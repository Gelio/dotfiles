#!/usr/bin/env node
// Merge settings-partial.json into ~/.claude/settings.json
//
// Usage:
//   node --experimental-strip-types setup-settings.ts
//
// Reads settings-partial.json (adjacent to this script) and deep-merges it
// into ~/.claude/settings.json. Semantics:
//   - Plain objects: recursive merge; partial values win at conflicting leaves.
//   - Arrays: union by structural equality (no duplicates; existing order kept).
//   - Scalars: partial overwrites existing.
//   - `hooks`: matcher-level merge — new hook commands appended per matcher,
//     existing ones preserved. Comparison uses type + command + `if`.
//
// Safe to run repeatedly. Keys absent from the partial file are never touched.
// Requires: Node.js 24+ (native type-stripping).

import { readFileSync, writeFileSync, existsSync, mkdirSync, copyFileSync, renameSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";

type JsonValue =
  | null
  | boolean
  | number
  | string
  | JsonValue[]
  | { [key: string]: JsonValue };

type JsonObject = { [key: string]: JsonValue };

interface HookCommand {
  type: string;
  command: string;
  if?: string;
}

interface HookMatcher {
  matcher: string;
  hooks: HookCommand[];
}

type HooksConfig = Record<string, HookMatcher[]>;

function isPlainObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function deepMerge(target: JsonValue, source: JsonValue): JsonValue {
  if (Array.isArray(target) && Array.isArray(source)) {
    const result: JsonValue[] = [...target];
    for (const item of source) {
      const serialized = JSON.stringify(item);
      if (!result.some((t) => JSON.stringify(t) === serialized)) {
        result.push(item);
      }
    }
    return result;
  }
  if (isPlainObject(target) && isPlainObject(source)) {
    const result: JsonObject = { ...target };
    for (const [key, value] of Object.entries(source)) {
      result[key] = key in result ? deepMerge(result[key], value) : value;
    }
    return result;
  }
  return source;
}

function mergeHooks(target: HooksConfig, source: HooksConfig): HooksConfig {
  const result: HooksConfig = { ...target };
  for (const [event, sourceMatchers] of Object.entries(source)) {
    const merged: HookMatcher[] = (result[event] ?? []).map((m) => ({
      ...m,
      hooks: [...m.hooks],
    }));
    for (const sourceMatcher of sourceMatchers) {
      const existing = merged.find((m) => m.matcher === sourceMatcher.matcher);
      if (existing) {
        for (const newHook of sourceMatcher.hooks) {
          const duplicate = existing.hooks.some(
            (h) =>
              h.type === newHook.type &&
              h.command === newHook.command &&
              h.if === newHook.if,
          );
          if (!duplicate) existing.hooks.push(newHook);
        }
      } else {
        merged.push(sourceMatcher);
      }
    }
    result[event] = merged;
  }
  return result;
}

const scriptDir = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const option = (name: string, fallback: string): string => {
  const index = args.indexOf(name);
  if (index < 0) return fallback;
  if (!args[index + 1] || args[index + 1].startsWith("--")) {
    throw new Error(`Missing value for ${name}`);
  }
  return args[index + 1];
};
const agent = option("--agent", "claude");
if (!["claude", "codex"].includes(agent)) throw new Error(`Unknown agent: ${agent}`);
const targetHome = option("--target-home", homedir());
const configDir = option("--config-dir", join(targetHome, `.${agent}`));
const settingsPath = join(configDir, agent === "claude" ? "settings.json" : "hooks.json");
const partialPath = join(scriptDir, agent === "claude" ? "settings-partial.json" : "codex-hooks-partial.json");

if (!existsSync(partialPath)) {
  console.error(`Error: ${partialPath} not found.`);
  process.exit(1);
}

const settings: JsonObject = existsSync(settingsPath)
  ? JSON.parse(readFileSync(settingsPath, "utf-8"))
  : {};

const partial: JsonObject = JSON.parse(readFileSync(partialPath, "utf-8"));

const { hooks: partialHooks, ...partialRest } = partial;
if (partialHooks) {
  const existingHooks = (settings.hooks as HooksConfig | undefined) ?? {};
  settings.hooks = mergeHooks(
    existingHooks,
    partialHooks as HooksConfig,
  ) as unknown as JsonValue;
}

const merged = deepMerge(settings, partialRest) as JsonObject;

const serialized = JSON.stringify(merged, null, 2) + "\n";
mkdirSync(configDir, { recursive: true });
if (!existsSync(settingsPath) || readFileSync(settingsPath, "utf-8") !== serialized) {
  if (existsSync(settingsPath)) {
    copyFileSync(settingsPath, `${settingsPath}.backup-${Date.now()}`);
  }
  const temporary = `${settingsPath}.tmp-${process.pid}`;
  writeFileSync(temporary, serialized, { mode: 0o600 });
  renameSync(temporary, settingsPath);
}
console.log(`Merged ${partialPath} into ${settingsPath}`);
