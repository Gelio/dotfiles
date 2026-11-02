#!/usr/bin/env bash
set -euo pipefail

echo "> For tmux bottom bar to work correctly, powerline icons are required"
echo "> Install a NerdFond like FiraCode NF or JetBrains Mono NF"

printf "\n\n"

"$(dirname -- "${BASH_SOURCE[0]}")/install-plugins.sh"
