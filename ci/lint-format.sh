#!/usr/bin/env bash
# Checks Markdown, JSON and YAML formatting. The files to skip are listed in
# .oxfmtrc.jsonc, so that the editor skips them too.
set -euo pipefail

ci_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$ci_dir/.."

"$ci_dir/source-files.sh" format | tr '\n' '\0' | xargs -0 oxfmt --check
