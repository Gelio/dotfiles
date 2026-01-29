#!/usr/bin/env bash
set -eou pipefail

if command -v brew >/dev/null && ! command -v protoc >/dev/null; then
  # NOTE: protobuf is required to install atuin from source
  echo "Installing protobuf via Homebrew"
  brew install protobuf
fi

cargo binstall atuin

./stow.sh
