#!/usr/bin/env bash
# Checks Lua formatting. No stylua.toml, so that StyLua reads .editorconfig the
# same way it does when the editor formats a file.
set -euo pipefail

ci_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$ci_dir/.."

"$ci_dir/source-files.sh" lua | tr '\n' '\0' | xargs -0 stylua --check
