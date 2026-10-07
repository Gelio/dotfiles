#!/usr/bin/env bash
set -euxo pipefail

include_my_config=$(
  cat <<EOF
[include]
  path = "~/.config/git.gitconfig"
EOF
)

important_line=$(echo "$include_my_config" | tail -n 1)

if grep -qF "$important_line" ~/.gitconfig; then
  echo "Already installed"
else
  echo "$include_my_config" >>~/.gitconfig
  echo "Installed correctly"
fi
