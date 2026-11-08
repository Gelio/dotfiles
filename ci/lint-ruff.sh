#!/usr/bin/env bash
# Lints and checks the formatting of Python files. Scripts with only a shebang
# are found by source-files.sh, since ruff's own discovery goes by extension.
set -euo pipefail

ci_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$ci_dir/.."

status=0
"$ci_dir/source-files.sh" python | tr '\n' '\0' | xargs -0 ruff check || status=1
"$ci_dir/source-files.sh" python | tr '\n' '\0' | xargs -0 ruff format --check || status=1
exit "$status"
