# Exploring Effect (Effect-TS) in the `worktrees` CLI

> **Status:** analysis only — no code or tooling was changed. Snippets below are
> illustrative sketches that live in this document, not in the codebase.

## Bottom line

**Do not adopt Effect now.** Effect is a powerful, well-engineered library, but
it is a *pervasive paradigm*, not a drop-in utility: adopting it idiomatically
rewrites essentially every async function in the engine and pulls in a large
dependency with a steep learning curve. That directly contradicts this
project's stated philosophy — a ~12-file, no-build, single-runtime-dependency
(`zx`) CLI that mostly shells out to `git`. The concrete wins Effect would buy
us here (typed errors, dependency injection for testability) are real but
**modest** for a tool this size, and ~80% of them are reachable with a tiny
hand-rolled result type plus a "services" object — at roughly 5% of the cost.

Revisit Effect only if the tool grows substantially: heavy concurrency
(parallel worktree operations with bounded fan-out), a long-running daemon /
watch mode, complex retry/backoff against flaky remotes, or a much larger
surface area where untyped error flow becomes genuinely hard to reason about.

---

## 1. What Effect offers that's relevant here

Effect is a single library bundling what would otherwise be many: a typed
effect system, dependency injection, structured concurrency, resource safety,
retry scheduling, and more. The pieces relevant to *this* codebase:

- **Typed errors.** Today errors are untyped: a value either succeeds or
  `throw`s/`die()`s, and the type system says nothing about *what* can fail.
  Effect encodes the error channel in the type: `Effect<A, E, R>` = "succeeds
  with `A`, may fail with `E`, needs services `R`". The compiler then forces
  every caller to handle (or explicitly propagate) each declared failure.
- **Dependency injection / services.** Side effects (`git`, filesystem,
  prompts, dynamic config `import()`) become *services* requested via the `R`
  channel and provided at the edge. This makes the engine testable without
  monkey-patching modules or shelling out to a real `git`.
- **Resource safety (`acquireRelease`).** Guarantees cleanup (e.g. always
  `rl.close()` a readline interface, always prune a half-created worktree on
  failure) even on interruption — a typed, composable `try/finally`.
- **Structured concurrency.** `Effect.forEach(..., { concurrency: n })`,
  interruption propagation, racing. Relevant only if we ever process multiple
  worktrees in parallel.
- **Retries / schedules.** `Effect.retry(effect, Schedule.exponential(...))`
  for flaky operations (e.g. a network `git fetch`).

How much of this do we actually need today? Typed errors and DI: somewhat. The
rest (concurrency, schedules, resource pools): essentially not yet — the engine
is sequential and I/O-bound on a local `git`.

---

## 2. Concrete before/after sketches (this codebase)

### 2a. `loadConfig` — untyped throw/`die` → typed failures

**Before** (`src/config.ts`): mixes `die()` (process exit, untyped) and `throw`,
so callers can't see what may go wrong.

```ts
export async function loadConfig(): Promise<LoadedConfig> {
  const repo = await repoRoot();              // may die("not inside a git repo")
  const source = resolveConfigSource(repo);
  if (!source) die(`no worktrees config for ${repo} — run: worktrees init`);
  const config = await importConfig(source);  // may throw (import / parse)
  await registerRepo(repo, source);           // may throw (fs)
  return { source, config, repo };
}
```

**After** (sketch): failures are values in the type.

```ts
class NotInRepo   extends Data.TaggedError("NotInRepo")<{}> {}
class NoConfig    extends Data.TaggedError("NoConfig")<{ repo: string }> {}
class ConfigImportError extends Data.TaggedError("ConfigImportError")<{
  source: string; cause: unknown;
}> {}

const loadConfig: Effect.Effect<
  LoadedConfig,
  NotInRepo | NoConfig | ConfigImportError,
  Git | FileSystem
> = Effect.gen(function* () {
  const repo = yield* repoRoot;                       // fails NotInRepo
  const source = yield* resolveConfigSource(repo);    // fails NoConfig
  const config = yield* importConfig(source);         // fails ConfigImportError
  yield* registerRepo(repo, source);
  return { source, config, repo };
});
```

The signature now *documents* the three failure modes, and the top-level
handler in `bin/worktrees.ts` becomes an exhaustive `match` over tagged errors
instead of `e instanceof Error ? e.message : String(e)`.

### 2b. The `git()` wrapper → a `Git` service

**Before** (`src/git.ts`): a free function bound directly to `zx`'s `$`, with
`repoRoot()` calling `die()` on failure. Hard to test without a real `git`.

```ts
import { $ } from 'zx';
export async function git(args: string[], cwd?: string): Promise<string> {
  const out = await (cwd ? $({ cwd })`git ${args}` : $`git ${args}`);
  return out.stdout.trim();
}
```

**After** (sketch): a service interface, so commands depend on `Git`, not on
`zx`. Tests provide a fake layer; production provides the `zx`-backed layer.

```ts
class GitError extends Data.TaggedError("GitError")<{
  args: string[]; exitCode: number; stderr: string;
}> {}

class Git extends Context.Tag("Git")<Git, {
  run: (args: string[], cwd?: string) => Effect.Effect<string, GitError>;
  ok:  (args: string[], cwd?: string) => Effect.Effect<boolean>;
}>() {}

const GitLive = Layer.succeed(Git, {
  run: (args, cwd) => Effect.tryPromise({
    try: () => (cwd ? $({ cwd })`git ${args}` : $`git ${args}`).then(o => o.stdout.trim()),
    catch: (cause) => new GitError({ args, exitCode: 1, stderr: String(cause) }),
  }),
  ok: (args, cwd) => Effect.promise(() =>
    (cwd ? $({ cwd })`git ${args}` : $`git ${args}`).nothrow().then(p => p.exitCode === 0)),
});
```

### 2c. Replacing `die()` with a typed boundary

**Before** (`src/log.ts` + `bin/worktrees.ts`): `die()` exits mid-flow from deep
in the call stack; the entry's `.catch` flattens everything to a string.

```ts
export function die(msg: string): never {
  console.error(chalk.red(`Error: ${msg}`));
  process.exit(1);
}
```

**After** (sketch): commands return effects with declared errors; only the entry
point decides exit codes, mapping each tagged error to a message.

```ts
const program = cmdSetup(argv).pipe(
  Effect.catchTags({
    NotInRepo: () => Console.error("Error: not inside a git repo"),
    NoConfig: (e) => Console.error(`Error: no config for ${e.repo} — run: worktrees init`),
  }),
);
Effect.runPromise(program.pipe(Effect.provide(AppLive)))
  .catch(() => process.exit(1));
```

---

## 3. Trade-offs (honest)

- **Effect is not incremental.** Idiomatic use means functions return
  `Effect<...>` rather than `Promise<...>`. Because effects compose only with
  effects, the type colonizes the call graph: convert `git()` and `loadConfig`
  and you are quickly converting `setup`, `sync`, `teardown`, `list`,
  `symlinks`, `ports`, and the entry point. You can wrap Effect at the edges
  with `runPromise`, but a *half-Effect* codebase gets the costs of both worlds.
- **It clashes with the project's minimalism.** The README's contract is
  explicit: minimal deps, configs import **only** `node:*`, no build step. Today
  the runtime tree is `zx` and that's it. Effect is a large addition to
  `node_modules` and a second core concept every contributor must learn.
- **No-build still works — but the engine grows.** `--experimental-strip-types`
  only strips type annotations; it doesn't care that `effect` is imported, so
  the run-via-`node` model survives, and **user configs are unaffected** (they
  still import only `node:*` — Effect would live in the engine, never in the
  injected `HookContext`). The cost is engine weight and startup: every
  subcommand is a fresh `node` process that now loads Effect before doing
  anything. For a CLI whose latency budget is dominated by spawning `git`, this
  is a real (if small) regression, and notable for the in-shell completion path
  that today avoids Node entirely.
- **Steep learning curve.** Generators, `Layer`/`Context`, tagged errors,
  `Schedule` — a meaningful ramp for a tool whose current code is
  plain-`async`/`await` readable by anyone.
- **Modest payoff at this size.** The genuine wins are typed errors and DI for
  tests. With ~12 files and a sequential, I/O-bound flow, the untyped error
  surface is small and already centralized in `die()`/`log.ts`, and the code is
  easy to follow. The features where Effect is transformative (structured
  concurrency, schedules, resource pools, fibers) are not exercised here yet.

### Trade-off summary

| Dimension | Today (`zx` + `die`) | With Effect |
|---|---|---|
| Dependencies | 1 runtime (`zx`) | `zx` + `effect` (large) |
| Build step | None (strip-types) | Still none |
| Typed errors | No (throw / `die`) | Yes (`E` channel) |
| Testability of I/O | Low (real `git`, fs) | High (service layers) |
| Resource safety | Manual `try/finally` | `acquireRelease` |
| Concurrency | None needed | First-class (unused today) |
| Retry/backoff | None | `Schedule` (unused today) |
| Startup cost / latency | Minimal | Higher (load Effect per invocation) |
| Learning curve | Low | High |
| Adoption shape | n/a | All-or-most (colonizing) |
| Config contract impact | n/a | None (configs stay `node:*`-only) |

---

## 4. Recommendation

**Not worth a full Effect adoption now.** The paradigm cost and dependency
weight outrun the benefit for a tool this small, and adoption can't be
meaningfully partial.

If the *benefits* (typed errors + testable I/O) are wanted, take a lighter
middle path that captures most of the value at a fraction of the cost — and
keeps zero new runtime dependencies and the no-build model intact:

1. **A tiny `Result` / discriminated-union error type.** Replace `die()` deep in
   the stack with returned, tagged failures; let only `bin/worktrees.ts` decide
   exit codes and messages.

   ```ts
   // sketch — a few lines, no dependency
   type Ok<A> = { ok: true; value: A };
   type Err<E> = { ok: false; error: E };
   type Result<A, E> = Ok<A> | Err<E>;

   type ConfigError =
     | { _tag: "NotInRepo" }
     | { _tag: "NoConfig"; repo: string }
     | { _tag: "ConfigImportError"; source: string; cause: unknown };
   ```

   This already removes the "untyped `throw`/`die`" complaint for the paths that
   matter, without changing the `Promise`-based control flow.

2. **A hand-rolled "services" object for testability.** Pass an injectable
   `{ git, fs, prompt }` bag (or a small `Deps` interface) into command
   functions instead of importing `zx`/`fs` directly. Tests supply fakes; prod
   supplies the `zx`/`node:fs` implementations. This buys the DI win behind
   Effect's `Layer`/`Context` with an ordinary TypeScript interface.

Together these address the two real motivations — typed errors and testable
side effects — at roughly **80% of the value for ~5% of the cost**, and they
stay faithful to the README's contract.

**When Effect *would* pay off:** if `worktrees` grows materially — parallel
operations across many worktrees with bounded concurrency, a long-running
watch/daemon mode, real retry/backoff against flaky remotes, or a surface large
enough that untyped error propagation becomes hard to reason about. At that
point Effect's concurrency, scheduling, resource safety, and typed-error model
start earning their weight, and the migration cost is justified by capabilities
that are genuinely hard to hand-roll well. Until then, the lighter middle path
is the better fit.
