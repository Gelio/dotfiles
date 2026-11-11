#!/usr/bin/env bash
# Lints every tracked Lua file. Selene reads selene.toml and neovim.yml from the
# working directory, so it runs from universal/neovim, including for files
# outside it.
set -euo pipefail

ci_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
repo_root="$ci_dir/.."

"$ci_dir/source-files.sh" lua | sed 's|^|../../|' | tr '\n' '\0' |
  (cd "$repo_root/universal/neovim" && xargs -0 selene)
