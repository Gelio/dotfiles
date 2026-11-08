#!/usr/bin/env bash
# Compares the mise hashes pinned in bootstrap.sh with the SHASUMS256.txt of the
# pinned release. Machines that already have mise never run that download, so a
# bad hash would otherwise show up only on a new machine.
#
# Exits 1 when a hash doesn't match, 2 when the check itself can't run.
#
# usage: check-mise-pin.sh [path/to/bootstrap.sh]
set -euo pipefail

bootstrap="${1:-universal/bootstrap.sh}"

version="$(sed -nE 's/^mise_version="([^"]+)"$/\1/p' "$bootstrap")"
pins="$(sed -nE 's/^ *((linux|macos)-(x64|arm64))\) expected_sha=([0-9a-f]{64}) ;;$/\1 \4/p' "$bootstrap")"
if [[ -z "$version" || "$(wc -l <<<"$pins")" -ne 4 ]]; then
  echo "Expected mise_version and four pinned hashes in $bootstrap, found:" >&2
  echo "version: '$version'" >&2
  echo "$pins" >&2
  exit 2
fi

if ! sums="$(curl -fsSL --retry 3 "https://github.com/jdx/mise/releases/download/v${version}/SHASUMS256.txt")"; then
  echo "Could not download SHASUMS256.txt for mise $version" >&2
  exit 2
fi

status=0
while read -r platform pinned; do
  name="mise-v${version}-${platform}"
  # The release lists its files with a ./ prefix
  published="$(awk -v name="$name" '{ file = $2; sub(/^\*?\.\//, "", file); if (file == name) print $1 }' <<<"$sums")"
  if [[ -z "$published" ]]; then
    echo "No $name in SHASUMS256.txt" >&2
    exit 2
  elif [[ "$published" != "$pinned" ]]; then
    echo "Hash mismatch for $platform: pinned $pinned, release has $published" >&2
    status=1
  else
    echo "$platform matches mise $version"
  fi
done <<<"$pins"
exit "$status"
