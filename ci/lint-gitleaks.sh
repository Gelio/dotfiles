#!/usr/bin/env bash
# Scans the whole history of HEAD for secrets. HEAD rather than gitleaks' default
# of every ref, so that local stashes and branches can't make a run differ from
# CI. This repo is public: only the rule, file and commit of a finding are
# printed, never its value.
set -euo pipefail

ci_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$ci_dir/.."

if [[ "$(git rev-parse --is-shallow-repository)" == true ]]; then
  echo "Shallow clone: the history scan needs fetch-depth: 0" >&2
  exit 1
fi

report="$(mktemp)"
trap 'rm -f "$report"' EXIT

if ! gitleaks git --no-banner --redact --log-level=warn \
  --log-opts='--full-history HEAD' \
  --report-format=json --report-path="$report" .; then
  jq -r '.[] | "\(.RuleID) \(.File):\(.StartLine) \(.Commit)"' "$report" >&2
  exit 1
fi
