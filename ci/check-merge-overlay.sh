#!/usr/bin/env bash
# Checks that machine-local overlays (mise/merge_local.py) reach the agents'
# settings: writes an overlay for ~/.claude/settings.json and
# ~/.codex/config.toml, applies, and looks for the overlay's entries next to
# the shared ones. Run after bootstrap installed the dotfiles with the ai group.
#
# NOTE: runs on macOS bash 3.2 too
set -euo pipefail

failed=0

function problem {
  echo "FAIL: $*" >&2
  failed=1
}

function jq_tool {
  mise x jq -- jq "$@"
}

local_dir="${XDG_CONFIG_HOME:-$HOME/.config}/dotfiles/local"
mkdir -p "$local_dir/.claude" "$local_dir/.codex"
cat >"$local_dir/.claude/settings.json" <<'EOF'
{ "sandbox": { "network": { "allowedDomains": ["overlay.example.com"] } } }
EOF
cat >"$local_dir/.codex/config.toml" <<'EOF'
[tui]
status_line = ["overlay-item"]
EOF

cd "$HOME"
mise dot apply

domains="$(jq_tool -c '.sandbox.network.allowedDomains' "$HOME/.claude/settings.json")"
[[ "$domains" == *'"github.com"'* ]] || problem "$HOME/.claude/settings.json lost the shared domains: $domains"
[[ "$domains" == *'"overlay.example.com"'* ]] || problem "$HOME/.claude/settings.json lacks the overlay's domain: $domains"

grep -q '"overlay-item"' "$HOME/.codex/config.toml" || problem "$HOME/.codex/config.toml lacks the overlay's status_line item"
grep -q '"weekly-limit"' "$HOME/.codex/config.toml" || problem "$HOME/.codex/config.toml lost the shared status_line items"

not_applied="$(mise dot status --json | jq_tool -r '.edits[] | select(.state != "applied") | "\(.path) (\(.state))"')"
[[ -z "$not_applied" ]] || problem "edits not applied after the overlay apply:"$'\n'"$not_applied"

if ((failed)); then
  exit 1
fi
echo "Overlay entries applied next to the shared ones"
