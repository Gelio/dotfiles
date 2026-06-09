# Rewriting `worktrees` in Rust, Zig, or Go — a feasibility analysis

> Scope: this is an architectural analysis only. No source, tooling, or behavior
> is changed. The question under review: *what would it take to rewrite this app
> in a compiled language, which is the best fit, and what are the trade-offs in
> performance, ease of development, and maintainability?*

## Executive summary (bottom line up front)

- **Performance is not the constraint.** `worktrees` is an I/O- and
  process-orchestration tool. It spends virtually all of its wall-clock time
  waiting on `git` subprocesses and the filesystem. A compiled language would
  not make `git worktree add` or symlink creation meaningfully faster. The only
  real perf win on the table is **cold-start** (skipping Node boot + TS
  type-stripping), measured in tens of milliseconds — irrelevant for a tool you
  run a handful of times a day.
- **The load-bearing feature is the config-as-code model.** Each repo's config
  is a TypeScript/JS module that the engine `import()`s at runtime, whose hooks
  (`postCreate`, `postSync`, `summary`) are *arbitrary user code* executed with
  zx's `$` and `chalk` injected in. **No compiled language can `import()` and
  run arbitrary user TypeScript** without either embedding a JS engine or
  redefining the config model. This is the central finding: a rewrite does not
  "port" this feature — it *replaces* it.
- **Recommendation: do not rewrite to gain performance.** If distribution
  (a single binary, no Node dependency) is the actual goal, the cheapest path is
  to stay in the TS/Node world and package it (Node SEA, Bun compile, or a
  bundler), **not** a language rewrite. If a language rewrite is mandated anyway,
  **Go** is the best fit (it is the lingua franca of git-orchestration CLIs and
  produces trivial static binaries); **Rust** only if memory safety/perf are
  prioritized over dev velocity; **Zig is not advisable** for this niche today.

---

## 1. What this app actually does (the workload)

Reading the source confirms a thin orchestration layer over `git` and the
filesystem:

- **Process orchestration.** `src/git.ts` shells out to `git` for every
  meaningful operation (`rev-parse --show-toplevel`, `worktree add`,
  `branch --show-current`, `reset --hard`, `diff --quiet`). zx's `$` is the
  subprocess runtime; setup is essentially "run `git worktree add`, then do
  filesystem bookkeeping."
- **Filesystem work.** `src/symlinks.ts` creates and merge-creates symlinks;
  `src/ports.ts` reads/writes a tiny line-oriented `.port-registry`;
  `src/config.ts` maintains a TSV `registry` file. All small-file `node:fs`
  calls.
- **A little interactive I/O.** `src/prompt.ts` uses `node:readline/promises`
  for `sync`/`teardown` selection; `list` formats a padded table.
- **Dynamic config load + hook dispatch.** `loadConfig()` discovers a config
  file, `import()`s it, applies defaults, and the command modules call the
  user's hooks with a `HookContext`.

**Implication:** the hot path is `git` + syscalls. CPU time inside the engine is
negligible. This is the single most important fact for the rewrite question:
**the language's raw speed is not where time goes.** Any rewrite is competing on
*distribution, startup, and ergonomics*, not throughput.

---

## 2. The load-bearing constraint: config-as-executable-TypeScript

This is the crux, and it is what makes a rewrite expensive in *capability*, not
just effort.

### What the current design does

- A repo's config is a `.mts/.ts/.mjs/.js` module that `export default`s a
  `WorktreesConfig` (`src/types.ts`). The engine resolves it
  (`resolveConfigSource`) and **dynamically `import()`s it** at runtime
  (`importConfig` in `src/config.ts`).
- The config is **not data** — `postCreate`, `postSync`, and `summary` are
  functions, i.e. arbitrary user code. They can do anything Node can:
  `await import('node:fs/promises')`, spawn processes, write `.env` files, etc.
- The engine **injects zx** (`$`, `chalk`) into the `HookContext` precisely so
  the config does *not* need its own `node_modules`. As `src/types.ts` notes, a
  dynamically-imported config resolves imports relative to its own realpath
  (the dotfiles checkout), where zx is not installed; injection sidesteps that
  and hands hooks shell ergonomics "for free."
- There is even a **security guard** built around the fact that config is
  executable: `configPathIsSafe` refuses an in-repo `.worktrees.*` unless it is a
  symlink resolving *outside* the repo — explicitly "RCE vectors, since the
  engine imports the resolved module."

The runtime model reinforces this: **no build step.** The shebang
`#!/usr/bin/env -S node --experimental-strip-types` (see `bin/worktrees.ts`)
runs TypeScript directly. Authoring a config is "write a `.mts`, get full type
hints from `WorktreesConfig`, run it" — no compile, no bundle.

### Why a compiled language cannot port this 1:1

A native Go/Rust/Zig binary has no JavaScript runtime. It cannot `import()` a
user's `.mts` and call `config.postCreate(ctx)`. You have exactly three options,
all of which are trade-offs rather than ports:

1. **Embed a JS engine** (V8 via rusty_v8/`deno_core`, QuickJS via bindings,
   or Goja for Go). This *keeps* the executable-config ergonomic — but you have
   now re-created a large part of what Node already gives you, inside a binary
   that is suddenly tens of MB, with a hand-rolled module loader, your own
   TypeScript transpile step (QuickJS/Goja don't strip TS types), and a
   re-implemented `$`/`chalk` injection bridge across the FFI boundary. This is
   the *opposite* of a simplification and is rarely worth it.

2. **Change the config model to declarative data** (TOML/JSON/YAML) for the
   static fields (`ports`, `portStep`, `symlinkTargets`, `mergeSymlinkDirs`),
   plus **hooks-as-shell-scripts**: instead of `postCreate(ctx)`, run a
   `post-create.sh` with the context passed as env vars (`WT_PATH`,
   `WT_PORTS_*`, `WT_BRANCH`, …). This is clean and idiomatic for a static
   binary, but it **loses the typed, in-editor-checked, single-file config** and
   the `$`/`chalk` ergonomics. Users trade a typed function for a shell script
   and a stringly-typed env contract.

3. **A compiled plugin system** (e.g. dynamically-loaded `.so`/dylib, or WASM
   plugins). Heavyweight, poor authoring ergonomics for a personal-tooling CLI,
   and a hard sell versus just writing a `.mts`.

**This is the whole ballgame.** The config-as-code model is the app's defining
ergonomic. A rewrite either drags a JS engine along (defeating most of the
point) or redefines configuration into data + scripts (a different, arguably
worse, product for this author's use case). Everything else — git shelling,
symlinks, port math — is trivially portable to any of the three languages.

---

## 3. Per-language assessment for *this* app

| Dimension | Go | Rust | Zig |
|---|---|---|---|
| Process orchestration | `os/exec` — excellent, idiomatic, the language is *built* for this | `std::process::Command` — solid; `duct`/`xshell` for ergonomics | `std.process.Child` — works, more manual, smaller ecosystem |
| CLI framework | Cobra / urfave/cli — mature, ubiquitous | `clap` — best-in-class, derive macros | mostly hand-rolled arg parsing |
| Filesystem / symlinks | `os`, `path/filepath` — complete | `std::fs`, `std::os::unix` — complete | `std.fs` — complete but lower-level |
| Interactive prompts | `bufio` / survey | `dialoguer` / `inquire` | hand-rolled |
| Cross-compile & distribution | trivial: `GOOS/GOARCH`, single static binary, no libc headaches | excellent via targets/`cross`; static needs musl target | excellent cross-compile (a Zig strength), single binary |
| Dev velocity for this task | very high — GC, simple concurrency, fast compiles | medium — borrow checker + async friction for an I/O glue tool | low — manual memory mgmt, immature libs, churny std |
| Maintainability (this niche) | high — boring, readable, huge precedent (git tools) | high but heavier — more ceremony than the problem needs | risky — pre-1.0, breaking std changes, tiny hiring/help pool |
| Embedded JS option (to keep TS config) | Goja (pure-Go JS, no TS, ES5/partial ES6) | `deno_core`/rusty_v8 (full V8, heavy) or QuickJS | QuickJS via C interop, all manual |
| Overall fit | **Best** | Good if safety/perf prioritized | Not advisable yet |

### Go

The natural choice. Go is the de-facto language of git-adjacent CLIs (`gh`, `lazygit`,
`git-town`, much of the container/devtools world). `os/exec` makes the `git.ts`
layer a near-mechanical port; `path/filepath` + `os.Symlink` cover
`symlinks.ts`; the registry/port files are trivial. Cobra gives subcommands,
flags, and — relevant here — **shell completion generation for free**, which
this project currently hand-maintains for zsh and bash. Static binaries
cross-compile with one env var and need no runtime. For the config problem, the
honest Go answer is **declarative data + shell-script hooks** (Goja exists but
can't run TypeScript and only partially supports modern JS, so it doesn't
preserve the ergonomic anyway). Dev velocity and long-term maintainability are
the strongest of the three for a tool of this shape and size.

### Rust

Technically excellent and would produce the smallest, fastest, safest binary —
but it optimizes for properties this app doesn't need. `clap` is the best CLI
library in any of the three; `std::process::Command` plus `xshell`/`duct`
handles subprocesses well. The costs: async/error-handling ceremony and
borrow-checker friction buy little for a tool that mostly awaits `git`, and
compile times slow the edit/run loop that the current no-build TS workflow makes
instant. Rust is the right call *only* if memory safety or single-binary
polish are explicitly prioritized over development speed. To keep the
executable-config ergonomic you'd embed V8 via `deno_core` — powerful (it could
even run TS via swc), but it turns a ~small CLI into a project that ships a
JS runtime, which is hard to justify.

### Zig

Not advisable for this project today. Zig's cross-compilation story is genuinely
excellent and the language is pleasant, but it is pre-1.0 with a std library that
still changes in breaking ways, a small ecosystem (no mature CLI/arg or prompt
libraries — you hand-roll), and a thin pool of examples/help for git-orchestration
CLIs. The manual memory management is pure overhead for a glue tool that does no
hot-loop allocation. The config problem would mean wiring QuickJS through C interop
by hand. The risk/reward is wrong for personal tooling that should be boring and
durable.

---

## 4. Recommendation

**Do not rewrite for performance — there is no performance problem to solve.**
The app waits on `git`; a faster language doesn't speed up `git`.

What a rewrite would **gain**:

- A single static binary — `curl`/copy and run, no `npm ci`, no `install.sh`
  dance, no `~/.local/share/worktrees` anchor symlink.
- No Node runtime requirement and no `--experimental-strip-types` /
  `Node ≥ 22.6` constraint (note the README's mise escape-hatch for repos
  pinning older Node — that whole class of friction disappears).
- Faster cold start (tens of ms). Marginal for this usage pattern.

What a rewrite would **lose**:

- The defining ergonomic: a **typed, editor-checked, single-file TS config whose
  hooks are real code** with zx's `$`/`chalk` injected. This becomes either
  data + shell scripts (stringly-typed) or a JS engine embedded in your binary.
- The **no-build, strip-types workflow** — author a `.mts` and run it. A
  compiled language reintroduces a build/release step for every change to the
  engine.
- Free reuse of the Node ecosystem (zx, `node:readline/promises`,
  `node:util parseArgs`) that the code leans on today.

**If a rewrite is mandated regardless: choose Go.** It is the best fit for
git-orchestration CLIs, gives trivial static binaries and free completion
generation, and keeps maintenance boring. Accept that the config model becomes
declarative TOML/JSON + shell-script hooks. Choose **Rust** only if
safety/binary-polish are first-class goals and the team accepts slower
iteration. **Avoid Zig** until it stabilizes and grows the surrounding library
ecosystem.

---

## 5. The pragmatic middle path (recommended over any rewrite)

If the *real* motivation is distribution rather than performance, solve
distribution without abandoning the language that gives this tool its ergonomics:

1. **Keep Node/TS as-is.** For a personal/dotfiles machine-wide CLI, the current
   `install.sh` + strip-types model is already lightweight and the config
   ergonomic is the product. This is the default recommendation.
2. **Ship a single executable from the existing TS** if "no Node install" is the
   goal:
   - **`node --experimental-sea`** (Single Executable Applications) bundles the
     app + a Node runtime into one binary — keeps all current code and the
     `import()`-able config story (the embedded Node can still load user
     configs), at the cost of binary size and the SEA build step.
   - **Bun** (`bun build --compile`) produces a single binary, runs TS natively
     (no strip-types flag), supports dynamic `import()` of user configs, and
     keeps zx-style ergonomics — arguably the lowest-friction way to get a
     standalone binary *while preserving the executable-TS-config model*.
   - **A bundler** (esbuild/`bun build`) to ship one `.mjs` if the goal is
     simply fewer moving parts than `npm ci` for zx.
3. **Only consider a Go rewrite** if you also decide to *redesign* configuration
   to declarative data + shell hooks for reasons independent of language (e.g.
   you want non-JS users to author configs without touching TS). In that case
   the rewrite and the config redesign are one project, and Go is the language.

**Bottom line:** the executable-TypeScript config is the heart of this tool. A
language rewrite trades that heart for distribution and cold-start wins this
workload doesn't need. Package the TS (Bun compile or Node SEA) if you want a
standalone binary; reach for Go only if you're independently choosing to make
configuration declarative.
