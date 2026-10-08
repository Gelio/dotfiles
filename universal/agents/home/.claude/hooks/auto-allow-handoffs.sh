#!/usr/bin/env bash
set -uo pipefail

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // ""')

[ -z "$FILE_PATH" ] && exit 0

case "$TOOL" in
  Read|Write|Edit) ;;
  *) exit 0 ;;
esac

# Resolve `..` and symlinks (agents can write links into the handoffs
# directory) before comparing, or a path could only appear to be inside it.
# realpath -m isn't on macOS, and Python resolves paths that don't exist yet.
{ read -r ROOT; read -r RESOLVED; } < <(python3 -c '
import os, sys
for path in sys.argv[1:]:
    print(os.path.realpath(os.path.expanduser(path)))
' "$HOME/.local/agent-handoffs" "$FILE_PATH") || exit 0

case "$RESOLVED" in
  "$ROOT"/*)
    jq -n '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"Auto-allow access to ~/.local/agent-handoffs (session-handoff skill)"}}'
    ;;
esac
