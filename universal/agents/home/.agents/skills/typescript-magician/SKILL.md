---
name: typescript-magician
description: Fixing TypeScript type errors and typing code strictly. Use when TypeScript fails to compile, or when writing generics, type guards or types that replace `any`.
metadata:
  credits:
    skill: typescript-magician
    author: Matteo Collina
    url: "https://github.com/mcollina/skills/tree/main/skills/typescript-magician"
---

# TypeScript types

1. Run the project's type check (its `typecheck` or `tsc` script, else
   `tsc --noEmit`) and read the full error before changing code.
2. Fix the cause: a missing constraint, a wrong inference, an untyped boundary.
   Reach for `as`, `!`, `any` or `@ts-expect-error` only when nothing else
   works, and say why in a comment beside it.
3. Type untrusted input (parsed JSON, API responses) as `unknown` and narrow it
   with a type guard, or with the schema library the project already uses.
4. Change only the types the task is about; leave other `any`s alone unless the
   user asks.
5. Run the type check again. Done when it passes with no new errors.
