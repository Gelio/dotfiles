#!/usr/bin/env bash
# Runs ShellCheck on bash and sh scripts. *.bashrc files have no shebang, so
# they are told which shell they are for.
set -euo pipefail

ci_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$ci_dir/.."

status=0
"$ci_dir/shell-files.sh" shebang | tr '\n' '\0' | xargs -0 shellcheck || status=1
"$ci_dir/shell-files.sh" bashrc | tr '\n' '\0' | xargs -0 shellcheck -s bash || status=1
exit "$status"
