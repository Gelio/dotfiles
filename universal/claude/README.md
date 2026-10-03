# Claude Code and Codex dotfiles

Shared skills, hook policy, desktop notifications, and session handoffs, with
separate adapters for Claude Code and Codex. The directory stays named `claude`
to preserve existing dotfiles links and entry points.

## Install

Requires Python 3, Node.js 24+, GNU Stow, and `jq` for the Claude handoff hook.
Codex hooks were checked with Codex CLI 0.160.0; Claude entry points with Claude
Code 2.1.288. Use a Codex release that supports lifecycle hooks.

```bash
./stow.sh                         # existing default: Claude settings
./stow.sh --agent both            # Claude + Codex settings
./stow.sh --agent codex           # Codex settings only
./stow.sh --agent both --dry-run   # preview links and handoff migration
python3 check-setup.py            # inspect installed links and registrations
```

Run the installer from any directory. All modes install the shared resource
links and adapter scripts; only the selected agents' settings are merged.
Settings use the standard `~/.claude` and `~/.codex` configuration locations.

The installer refuses unmanaged Stow conflicts. Existing unrelated settings,
hooks, permission entries, and Claude plugin selections are preserved. Changed
settings receive timestamped backups beside the original file. Reinstalling
identical settings does not create another backup or duplicate hook entries.
Codex's `config.toml`, model, and sandbox preferences are left under your control.

For an isolated installation without modifying your home:

```bash
python3 install.py --agent both --target-home /tmp/agent-test-home
```

Restart the agents after installation. Codex must review and trust the new hook
commands before they execute; installation does not bypass that native review.

## Ownership and layout

| Source | Installed destination | Owner |
| --- | --- | --- |
| `stowed/.agents/skills/<name>/` | `~/.agents/skills/<name>/` | Stow; editable authored skills |
| `stowed/.claude/skills/<name>` | `~/.claude/skills/<name>` | Stow; compatibility links to authored skills |
| `stowed/.agents/lib/agent_setup/` | `~/.agents/lib/agent_setup/` | Stow; shared Python services |
| `stowed/.claude/`, `stowed/.codex/` | Agent-specific script locations | Stow; hook transport and UI adapters |
| `settings-partial.json` | `~/.claude/settings.json` | Additive settings merger |
| `codex-hooks-partial.json` | `~/.codex/hooks.json` | Additive settings merger |
| `stowed/.agents/.skill-lock.json` | `~/.agents/.skill-lock.json` | `npx skills`; tracked installation selections |
| Third-party skill content | Agent Skills CLI installation paths | `npx skills` |

Edit authored skills at their shared source. Do not install a third-party skill
with the same name over a Stow-owned skill. Claude paths remain valid, including
paths installed before this refactor. Codex discovers authored skills directly
in the common Agent Skills directory.

The authored skills cover commits, PR descriptions/comments, decision rationale,
TODO workflows, TODO enrichment, commit verification, diff walkthroughs, Jira
preferences, and session handoffs. Agent-specific commit attribution is documented
in `commit-conventions/references/attribution.md`.

## Hooks and notifications

| Capability | Claude | Codex |
| --- | --- | --- |
| Risky command checks | Existing `PreToolUse` entry point | `PreToolUse` adapter |
| Commit-file and attribution checks | Claude model trailer | Codex trailer |
| Fixup-scope advice | `PostToolUse` | `PostToolUse` |
| Launch repository capture | Session/environment fallback | SessionStart context; explicit project argument |
| Permission, completion, dismissal notifications | Existing notification entry points | Codex event adapter |
| Handoff file auto-allow | Claude-specific file/permission hook | Native sandbox access through `--add-dir` |
| Playwright sandbox exception | Claude-specific adapter | Codex controls its own sandbox |
| Status line and MCP call logging | Existing Claude scripts | No automatic translation |

Command policy and notification backends live in shared Python modules. Claude's
registered command paths are retained: the additive merger would otherwise leave
old hooks installed alongside renamed ones. Hook checks are guardrails, not a
complete shell parser or sandbox boundary.

Notifications use `terminal-notifier` on macOS and native Windows toasts on WSL.
They remain silent on other platforms. Notification groups distinguish Claude
and Codex; focused terminals suppress notifications as before.

## Shared handoffs

The store is `~/.local/agent-handoffs/<repo-key>/`. Installation migrates the old
`~/.local/claude-handoffs` store and leaves a compatibility symlink, preserving
existing handoff chains and already-running Claude sessions.

Migration checks all conflicts first. If both stores exist, matching files are
preserved and the legacy directory is backed up before its name becomes a link.
Different files at the same destination abort migration without overwriting.

```bash
python3 migrate-handoff-storage.py --dry-run
list-handoffs
codex-agent                      # codex with the shared store writable
# Equivalent when using the original Codex command:
codex --add-dir "$HOME/.local/agent-handoffs"
```

Origins are stored per agent/session, preventing collisions. Claude keeps its
existing environment fallback. Codex receives the launch repository through
SessionStart context and passes it explicitly to the handoff scripts, so a later
`cd` does not redirect the handoff. Both agents use the same Markdown format and
validators. Starting Codex with `--add-dir` grants access; hooks do not alter
sandbox permissions.

## Codex sandbox and approval prompts

For sandboxed work with automatic review of eligible approval requests:

```bash
codex-agent --approve-for-me
```

Equivalent defaults in `~/.codex/config.toml` are:

```toml
sandbox_mode = "workspace-write"
approval_policy = "on-request"
approvals_reviewer = "auto_review"
```

For sandboxed work that denies escalation requests without asking:

```bash
codex-agent --sandbox workspace-write --ask-for-approval never
```

`never` can prevent commits or other operations on protected paths. Auto-review
keeps the sandbox and reviews eligible requests instead. Hook trust is a separate
native review step. These choices are documented here rather than automatically
replacing your existing Codex settings.

See [Auto-review](https://learn.chatgpt.com/docs/sandboxing/auto-review) and
[agent approvals](https://learn.chatgpt.com/docs/agent-approvals-security).

## Third-party skills and plugins

Restore recorded third-party skill selections separately:

```bash
python3 bootstrap-skills.py                  # print commands
python3 bootstrap-skills.py --apply          # install for Claude and Codex
python3 bootstrap-skills.py --agent codex    # print Codex-only commands
npx skills update -g                        # normal upstream updates
```

This uses sources and skill names from `.skill-lock.json`. The recorded folder
hashes are not Git revision pins: restoration fetches upstream content and is
not an exact historical snapshot. It does not reinstall authored skills.

Plugin installation remains agent-specific:

| Existing Claude capability | Reuse strategy |
| --- | --- |
| Context7 / other MCP connections | Connect the same server separately in Codex; credentials and tool approvals remain local |
| Superpowers / review workflow plugins | Install a supported Codex integration explicitly; do not duplicate skills already installed standalone |
| TypeScript / Go LSP plugins | Keep Claude's native LSP plugins; evaluate Codex tooling separately |
| Claude settings / CLAUDE.md management | Keep Claude-specific |
| Security hooks | Keep native registration; shared local command policy runs independently |

`enabledPlugins` and the Caveman/Ponytail installation scripts remain Claude
configuration. This refactor does not copy plugin identifiers, credentials, or
MCP permission strings into Codex.

## Settings review

```bash
node --experimental-strip-types review-settings.ts
```

Review remains Claude-specific. Adopt portable Claude settings into
`settings-partial.json`; ignore machine-specific entries using
`.settings-review-ignore.json`. Codex hook registrations are maintained in
`codex-hooks-partial.json`. Hooks installed by another integration retain that
integration's ownership; do not adopt them unless you intend to maintain them.

## Validation and rollback

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s stowed/.agents/skills/session-handoff/evals -p 'test_*.py'
python3 tests/check_codex_runtime.py          # native discovery, temporary home
python3 check-setup.py
```

Tests cover additive/idempotent installation, unmanaged conflicts, existing
Python caches, agent attribution, fixup advice, notifications, origin isolation,
and shared handoff storage. Native Codex discovery does not call a model or trust
hooks. The existing `skill-evals` harness tests instruction bodies through Claude;
it does not establish automatic skill activation or real tool execution.

Reverting a commit does not undo settings merges. Restore the appropriate
`settings.json.backup-*` / `hooks.json.backup-*` file, then reinstall the reverted
layout. Keep the legacy handoff symlink: old versions can use the shared store
through that path. Disabling the Codex hook registrations does not affect Claude.
