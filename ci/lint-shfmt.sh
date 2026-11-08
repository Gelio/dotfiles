#!/usr/bin/env bash
# Checks shell formatting. No style flags, so that shfmt reads .editorconfig.
# The list is explicit because `shfmt -f` doesn't find *.bashrc files.
set -euo pipefail

ci_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$ci_dir/.."

{
  "$ci_dir/shell-files.sh" shebang
  "$ci_dir/shell-files.sh" bashrc
} | tr '\n' '\0' | xargs -0 shfmt -d
