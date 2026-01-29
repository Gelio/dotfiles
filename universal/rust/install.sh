#!/usr/bin/env bash
set -euo pipefail

# https://www.rust-lang.org/tools/install
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

./stow.sh

# Source to be able to run cargo in this script
source "$HOME/.cargo/env"
cargo binstall cargo-update
# Install cargo-binstall first, so further commands can use it for faster installs
cargo binstall cargo-binstall
cargo binstall git-stack
cargo binstall git-branch-stash-cli
cargo binstall --locked git-branchless

case "$(uname -s)" in
Darwin)
  # Cargo completions cannot be sourced inline. They must come from a regular file.
  rustup completions zsh cargo >~/.zfunc/_cargo
  ;;
Linux)
  # https://github.com/sfackler/rust-openssl/issues/763#issuecomment-339269157
  sudo apt install libssl-dev
  ;;
esac
