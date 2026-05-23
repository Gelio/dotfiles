#!/usr/bin/env node
// Review ~/.claude/settings.json for items to adopt into settings-partial.json.
//
// Usage:
//   node --experimental-strip-types review-settings.ts
//
// For each value in the live settings that isn't already contributed by the
// partial, print the item and prompt:
//   [a]dopt        — write the item into settings-partial.json
//   [s]kip         — skip for this run (ask again next time)
//   [i]gnore       — add to .settings-review-ignore.json (never ask again)
//   [q]uit         — stop reviewing and save what's been chosen so far
//
// Semantics mirror setup-settings.ts:
//   - Nested objects are walked per-leaf.
//   - Arrays are diffed by structural equality of elements.
//   - `hooks` is walked matcher-by-matcher and command-by-command.
//
// Requires Node.js 24+ (native type-stripping).

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";
import { createInterface, type Interface } from "node:readline";
import { stdin, stdout } from "node:process";

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

type Candidate =
  | { kind: "set"; path: string[]; value: JsonValue }
  | { kind: "arrayAdd"; path: string[]; value: JsonValue }
  | { kind: "hookMatcherAdd"; event: string; matcher: HookMatcher }
  | {
      kind: "hookCommandAdd";
      event: string;
      matcherPattern: string;
      hook: HookCommand;
    };

function isPlainObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function* findCandidates(
  partial: JsonObject,
  live: JsonObject,
): Generator<Candidate> {
  for (const [key, liveValue] of Object.entries(live)) {
    if (key === "hooks") {
      const p = (partial.hooks as unknown as HooksConfig | undefined) ?? {};
      yield* findHookCandidates(p, liveValue as unknown as HooksConfig);
    } else {
      yield* findGenericCandidates([key], partial[key], liveValue);
    }
  }
}

function* findGenericCandidates(
  path: string[],
  partial: JsonValue | undefined,
  live: JsonValue,
): Generator<Candidate> {
  if (isPlainObject(live)) {
    const p = isPlainObject(partial) ? partial : undefined;
    for (const [k, v] of Object.entries(live)) {
      yield* findGenericCandidates([...path, k], p?.[k], v);
    }
    return;
  }
  if (Array.isArray(live)) {
    const p = Array.isArray(partial) ? partial : [];
    for (const item of live) {
      const serialized = JSON.stringify(item);
      if (!p.some((pp) => JSON.stringify(pp) === serialized)) {
        yield { kind: "arrayAdd", path, value: item };
      }
    }
    return;
  }
  if (JSON.stringify(partial) !== JSON.stringify(live)) {
    yield { kind: "set", path, value: live };
  }
}

function* findHookCandidates(
  partial: HooksConfig,
  live: HooksConfig,
): Generator<Candidate> {
  for (const [event, liveMatchers] of Object.entries(live)) {
    const partialMatchers = partial[event] ?? [];
    for (const liveMatcher of liveMatchers) {
      const pm = partialMatchers.find((m) => m.matcher === liveMatcher.matcher);
      if (!pm) {
        yield { kind: "hookMatcherAdd", event, matcher: liveMatcher };
        continue;
      }
      for (const hook of liveMatcher.hooks) {
        const duplicate = pm.hooks.some(
          (h) =>
            h.type === hook.type &&
            h.command === hook.command &&
            h.if === hook.if,
        );
        if (!duplicate) {
          yield {
            kind: "hookCommandAdd",
            event,
            matcherPattern: liveMatcher.matcher,
            hook,
          };
        }
      }
    }
  }
}

function candidateKey(c: Candidate): string {
  switch (c.kind) {
    case "set":
      return c.path.join(".");
    case "arrayAdd":
      return `${c.path.join(".")}[]:${JSON.stringify(c.value)}`;
    case "hookMatcherAdd":
      return `hooks.${c.event}[matcher=${JSON.stringify(c.matcher.matcher)}]`;
    case "hookCommandAdd": {
      const h: HookCommand = {
        type: c.hook.type,
        command: c.hook.command,
        ...(c.hook.if ? { if: c.hook.if } : {}),
      };
      return `hooks.${c.event}[matcher=${JSON.stringify(c.matcherPattern)}].hooks:${JSON.stringify(h)}`;
    }
  }
}

function candidateHeading(c: Candidate): string {
  switch (c.kind) {
    case "set":
      return `Set ${c.path.join(".")}`;
    case "arrayAdd":
      return `Append to ${c.path.join(".")}`;
    case "hookMatcherAdd":
      return `Add hook matcher  hooks.${c.event}[matcher=${JSON.stringify(c.matcher.matcher)}]`;
    case "hookCommandAdd":
      return `Add hook command  hooks.${c.event}[matcher=${JSON.stringify(c.matcherPattern)}]`;
  }
}

function candidateBody(c: Candidate): JsonValue {
  switch (c.kind) {
    case "set":
    case "arrayAdd":
      return c.value;
    case "hookMatcherAdd":
      return c.matcher as unknown as JsonValue;
    case "hookCommandAdd":
      return c.hook as unknown as JsonValue;
  }
}

function getOrCreateObject(parent: JsonObject, key: string): JsonObject {
  if (!isPlainObject(parent[key])) parent[key] = {};
  return parent[key] as JsonObject;
}

function applyCandidate(partial: JsonObject, c: Candidate): void {
  if (c.kind === "hookMatcherAdd" || c.kind === "hookCommandAdd") {
    const hooks = getOrCreateObject(partial, "hooks") as unknown as HooksConfig;
    const matchers = (hooks[c.event] ??= []);
    if (c.kind === "hookMatcherAdd") {
      matchers.push(c.matcher);
      return;
    }
    let m = matchers.find((mm) => mm.matcher === c.matcherPattern);
    if (!m) {
      m = { matcher: c.matcherPattern, hooks: [] };
      matchers.push(m);
    }
    m.hooks.push(c.hook);
    return;
  }
  let cursor = partial;
  for (let i = 0; i < c.path.length - 1; i++) {
    cursor = getOrCreateObject(cursor, c.path[i]);
  }
  const last = c.path[c.path.length - 1];
  if (c.kind === "set") {
    cursor[last] = c.value;
  } else {
    if (!Array.isArray(cursor[last])) cursor[last] = [];
    (cursor[last] as JsonValue[]).push(c.value);
  }
}

const scriptDir = dirname(fileURLToPath(import.meta.url));
const settingsPath = join(homedir(), ".claude", "settings.json");
const partialPath = join(scriptDir, "settings-partial.json");
const ignorePath = join(scriptDir, ".settings-review-ignore.json");

if (!existsSync(settingsPath)) {
  console.error(`Error: ${settingsPath} not found.`);
  process.exit(1);
}
if (!existsSync(partialPath)) {
  console.error(`Error: ${partialPath} not found.`);
  process.exit(1);
}

const live: JsonObject = JSON.parse(readFileSync(settingsPath, "utf-8"));
const partial: JsonObject = JSON.parse(readFileSync(partialPath, "utf-8"));
const ignoreList: string[] = existsSync(ignorePath)
  ? JSON.parse(readFileSync(ignorePath, "utf-8"))
  : [];
const ignoreSet = new Set(ignoreList);

const candidates: Candidate[] = [...findCandidates(partial, live)].filter(
  (c) => !ignoreSet.has(candidateKey(c)),
);

if (candidates.length === 0) {
  console.log("No new items to review.");
  process.exit(0);
}

console.log(`Found ${candidates.length} item(s) to review.\n`);

const rl: Interface = createInterface({ input: stdin });
const lineIterator = rl[Symbol.asyncIterator]();

async function readLine(): Promise<string | null> {
  const { value, done } = await lineIterator.next();
  return done ? null : value;
}

let adopted = 0;
const newIgnores: string[] = [];
let quit = false;

for (const [i, c] of candidates.entries()) {
  if (quit) break;
  stdout.write(`\n── [${i + 1}/${candidates.length}] ${candidateHeading(c)}\n`);
  stdout.write(JSON.stringify(candidateBody(c), null, 2) + "\n");
  while (true) {
    stdout.write("[a]dopt / [s]kip / [i]gnore / [q]uit > ");
    const raw = await readLine();
    if (raw === null) {
      quit = true;
      break;
    }
    const answer = raw.trim().toLowerCase();
    if (answer === "a" || answer === "adopt") {
      applyCandidate(partial, c);
      adopted++;
      break;
    }
    if (answer === "s" || answer === "skip" || answer === "") break;
    if (answer === "i" || answer === "ignore") {
      newIgnores.push(candidateKey(c));
      break;
    }
    if (answer === "q" || answer === "quit") {
      quit = true;
      break;
    }
    stdout.write("  (use a/s/i/q)\n");
  }
}
rl.close();

if (adopted > 0) {
  writeFileSync(partialPath, JSON.stringify(partial, null, 2) + "\n");
  console.log(`\nAdopted ${adopted} item(s) into ${partialPath}`);
}
if (newIgnores.length > 0) {
  const updated = [...new Set([...ignoreList, ...newIgnores])].sort();
  writeFileSync(ignorePath, JSON.stringify(updated, null, 2) + "\n");
  console.log(`Added ${newIgnores.length} path(s) to ${ignorePath}`);
}
if (adopted === 0 && newIgnores.length === 0) {
  console.log("\nNo changes written.");
}
