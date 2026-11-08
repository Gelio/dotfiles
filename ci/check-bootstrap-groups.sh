#!/usr/bin/env bash
# Checks that groups=(...) in bootstrap.sh lists exactly the config.<group>.toml
# files. config.local.toml is the per-machine file, not a group.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

listed="$(sed -nE 's/^groups=\((.*)\)$/\1/p' universal/bootstrap.sh | tr ' ' '\n' | sort)"
on_disk="$(find universal/mise/config -maxdepth 1 -name 'config.*.toml' ! -name config.local.toml |
  sed -E 's/.*config\.(.*)\.toml$/\1/' | sort)"

if [[ -z "$listed" || "$listed" != "$on_disk" ]]; then
  echo "groups=(...) in universal/bootstrap.sh doesn't match universal/mise/config:" >&2
  diff <(echo "$listed") <(echo "$on_disk") >&2 || true
  exit 1
fi
echo "All $(wc -l <<<"$listed" | tr -d ' ') groups match their config files"
