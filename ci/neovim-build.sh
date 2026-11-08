#!/usr/bin/env bash
# Builds the Neovim commit pinned in universal/neovim/neovim-commit and installs
# it into the given prefix. CI uses this. Machines use universal/neovim/install.sh,
# which reads the same pin.
set -euo pipefail

prefix="${1:?usage: neovim-build.sh PREFIX}"
ci_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
commit="$(<"$ci_dir/../universal/neovim/neovim-commit")"

source_dir="$(mktemp -d)"
git init --quiet "$source_dir"
git -C "$source_dir" remote add origin https://github.com/neovim/neovim.git
git -C "$source_dir" fetch --quiet --depth=1 origin "$commit"
git -C "$source_dir" checkout --quiet FETCH_HEAD

make -C "$source_dir" CMAKE_BUILD_TYPE=RelWithDebInfo CMAKE_INSTALL_PREFIX="$prefix"
make -C "$source_dir" install
