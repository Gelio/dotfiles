---
name: session-handoff
description: "Creates comprehensive handoff documents for seamless AI agent session transfers. Triggered when: (1) user requests handoff/memory/context save, (2) context window approaches capacity, (3) major task milestone completed, (4) work session ending, (5) user says 'save state', 'create handoff', 'I need to pause', 'context is getting full', (6) resuming work with 'load handoff', 'resume from', 'continue where we left off'. Proactively suggests handoffs after substantial work (multiple file edits, complex debugging, architecture decisions). Solves long-running agent context exhaustion by enabling fresh agents to continue with zero ambiguity."
---

# Handoff

Creates comprehensive handoff documents that enable fresh AI agents to seamlessly continue work with zero ambiguity. Solves the long-running agent context exhaustion problem.

## Mode Selection

Determine which mode applies:

**Creating a handoff?** User wants to save current state, pause work, or context is getting full.
- Follow: CREATE Workflow below

**Resuming from a handoff?** User wants to continue previous work, load context, or mentions an existing handoff.
- Follow: RESUME Workflow below

**Proactive suggestion?** After substantial work (5+ file edits, complex debugging, major decisions), suggest:
> "We've made significant progress. Consider creating a handoff document to preserve this context for future sessions. Say 'create handoff' when ready."

## CREATE Workflow

### Step 1: Generate Scaffold

Run the smart scaffold script to create a pre-filled handoff document:

```bash
python scripts/create_handoff.py [task-slug]
```

Example: `python scripts/create_handoff.py implementing-user-auth`

**For continuation handoffs** (linking to previous work):
```bash
python scripts/create_handoff.py "auth-part-2" --continues-from 2024-01-15-auth.md
```

The script will:
- Create the centralized handoffs directory (`~/.local/claude-handoffs/<repo-key>/`) if needed
- Generate timestamped filename
- Pre-fill: timestamp, project path, git branch, recent commits, modified files
- Add handoff chain links if continuing from previous
- Output file path for editing

### Step 2: Complete the Handoff Document

Open the generated file and fill in all `[TODO: ...]` sections. Prioritize these sections:

1. **Current State Summary** - What's happening right now
2. **Important Context** - Critical info the next agent MUST know
3. **Immediate Next Steps** - Clear, actionable first steps
4. **Decisions Made** - Choices with rationale (not just outcomes)

Use the template structure in [references/handoff-template.md](references/handoff-template.md) for guidance.

**Write file paths relative to the repo root** (the `Project:` value in the
metadata) — e.g. `src/api/handlers.py`, not a path relative to whatever
subdirectory you happen to be working in. The resuming agent only has the
`Project:` root to navigate from, and `validate_handoff.py` resolves references
against it. (The validator also matches by path-suffix as a safety net, but
root-relative paths are unambiguous and the right thing for the next agent.)

**Never write secret values into the handoff — record names, not values.** When
you capture environment state, config, or setup steps, write the variable *name*
and what it's for (`DATABASE_URL` — prod Postgres connection string), never the
literal value. If a secret appears in the session context (an API key, password,
token, connection string with embedded credentials), redact it to a placeholder
(`sk_live_…`, `postgres://USER:PASSWORD@host/db`) as you write — the next agent
re-supplies it from their own environment, so the value is never needed and a
leaked handoff shouldn't expose it. Do this inline while writing; don't rely on
`validate_handoff.py` to catch it after the fact (it's a safety net, not the
mechanism). A redacted handoff is still complete — redact and continue rather
than refusing to produce the document.

Crucially, **don't echo the secret value back even to explain what you
redacted.** Say "I redacted the DB password and Stripe key" — never repeat the
literal value in your summary, your confirmation message, or a "here's what I
left out" note. Naming the value anywhere (document *or* surrounding reply) puts
it in the transcript and defeats the redaction.

### Step 3: Validate the Handoff

Run the validation script to check completeness and security:

```bash
python scripts/validate_handoff.py <handoff-file>
```

The validator checks:
- [ ] No `[TODO: ...]` placeholders remaining
- [ ] Required sections present and populated
- [ ] No potential secrets detected (API keys, passwords, tokens)
- [ ] Referenced files exist
- [ ] Quality score (0-100)

**If the validator flags a secret, redact that value to a placeholder and re-run — don't finalize with secrets present, and don't abandon the handoff over it.** Likewise raise a score below 70 by filling the gaps it names.

### Step 4: Confirm Handoff

Report to user:
- Handoff file location
- Validation score and any warnings
- Summary of captured context
- First action item for next session

## RESUME Workflow

### Step 1: Find Available Handoffs

List handoffs in the current project:

```bash
python scripts/list_handoffs.py
```

This shows all handoffs with dates, titles, and completion status.

### Step 2: Check Staleness

Before loading, check how current the handoff is:

```bash
python scripts/check_staleness.py <handoff-file>
```

Staleness levels:
- **FRESH**: Safe to resume - minimal changes since handoff
- **SLIGHTLY_STALE**: Review changes, then resume
- **STALE**: Verify context carefully before resuming
- **VERY_STALE**: Consider creating a fresh handoff

The script checks:
- Time since handoff was created
- Git commits since handoff
- Files changed since handoff
- Branch divergence
- Missing referenced files

### Step 3: Load the Handoff

Read the relevant handoff document completely before taking any action.

If handoff is part of a chain (has "Continues from" link), also read the linked previous handoff for full context.

### Step 4: Verify Context

Follow the checklist in [references/resume-checklist.md](references/resume-checklist.md):

1. Verify project directory and git branch match
2. Check if blockers have been resolved
3. Validate assumptions still hold
4. Review modified files for conflicts
5. Check environment state

### Step 5: Begin Work

Start with "Immediate Next Steps" item #1 from the handoff document.

Reference these sections as you work:
- "Critical Files" for important locations
- "Key Patterns Discovered" for conventions to follow
- "Potential Gotchas" to avoid known issues

### Step 6: Update or Chain Handoffs

As you work:
- Mark completed items in "Pending Work"
- Add new discoveries to relevant sections
- For long sessions: create a new handoff with `--continues-from` to chain them

## Handoff Chaining

For long-running projects, chain handoffs together to maintain context lineage:

```
handoff-1.md (initial work)
    ↓
handoff-2.md --continues-from handoff-1.md
    ↓
handoff-3.md --continues-from handoff-2.md
```

Each handoff in the chain:
- Links to its predecessor
- Can mark older handoffs as superseded
- Provides context breadcrumbs for new agents

When resuming from a chain, read the most recent handoff first, then reference predecessors as needed.

## Storage Location

Handoffs are stored in a **single centralized location**, keyed by repository:

```
~/.local/claude-handoffs/<repo-key>/YYYY-MM-DD-HHMMSS-[slug].md
```

`<repo-key>` is the origin repo's path with separators replaced by `-`
(e.g. `-Users-me-ubuntu-dotfiles`), mirroring Claude Code's own project-dir
encoding. The handoff's real repo path is also recorded in its `Project:`
metadata, which `check_staleness.py` uses for git comparisons.

Why centralized rather than inside each repo: a repo-local `.claude/handoffs/`
can sit *above* the session's launch directory, and the OS command sandbox only
grants writes to concrete paths (not globs), so writing up to a parent repo root
gets blocked. One fixed root (`~/.local/claude-handoffs`, added once to
`sandbox.filesystem.allowWrite`) is writable from any working directory, immune
to `cd`, subdirectory launches, and multi-agent work.

Why `~/.local/` and **not** `~/.claude/`: Claude Code treats every write under
`~/.claude/` as a potential settings edit and raises an "allow Claude to edit its
own settings" prompt that no permission rule or hook can suppress.

The **repo** a handoff belongs to is resolved as follows (see
`scripts/_handoff_paths.py::resolve_project_root`):

1. An explicit `--project-dir` passed to `create_handoff.py`.
2. The origin captured at SessionStart by `hooks/capture-handoff-origin.py`
   (`~/.local/claude-handoffs/.origins/<session_id>`) — the git toplevel of the
   launch directory, immune to any later `cd`.
3. `$CLAUDE_PROJECT_DIR` resolved to its git toplevel.
4. The current directory's git toplevel, then the current directory itself.

Naming convention: `YYYY-MM-DD-HHMMSS-[slug].md`

Example: `2024-01-15-143022-implementing-auth.md`

## Resources

### scripts/

| Script | Purpose |
|--------|---------|
| `create_handoff.py [slug] [--continues-from <file>]` | Generate new handoff with smart scaffolding |
| `list_handoffs.py [path]` | List available handoffs in a project |
| `validate_handoff.py <file>` | Check completeness, quality, and security |
| `check_staleness.py <file>` | Assess if handoff context is still current |
| `migrate_handoffs.py [repo ...] [--dry-run]` | Move repo-local handoffs into the centralized store |

### references/

- [handoff-template.md](references/handoff-template.md) - Complete template structure with guidance
- [resume-checklist.md](references/resume-checklist.md) - Verification checklist for resuming agents
