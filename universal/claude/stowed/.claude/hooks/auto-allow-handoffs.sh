#!/usr/bin/env bash
set -uo pipefail

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // ""')

[ -z "$FILE_PATH" ] && exit 0

case "$TOOL" in
  Read|Write|Edit)
    if echo "$FILE_PATH" | grep -qE '\.claude/handoffs/'; then
      jq -n '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"Auto-allow access to .claude/handoffs (session-handoff skill)"}}'
    fi
    ;;
esac
