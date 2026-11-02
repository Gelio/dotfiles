#!/usr/bin/env bash

set -euo pipefail

pushd ~/.local/ >/dev/null
if [[ -d tmux ]]; then
  cd tmux
  echo "tmux repository found, pulling latest changes"
  git pull
else
  echo "tmux repository not found, cloning it for the first time"
  git clone https://github.com/tmux/tmux.git
  cd tmux

  # https://github.com/tmux/tmux/wiki/Installing#from-source-tarball
  echo "Installing build dependencies"
  sudo apt install libevent-dev bison
fi
echo "Compiling tmux"
sh autogen.sh
./configure
make
sudo make install
popd >/dev/null

./stow.sh

echo "> Make sure to run the install script from the universal folder"

source ../bash-completions-dir.sh
completions_path=$BASH_COMPLETIONS_DIR/tmux.bash

if [ -f "$completions_path" ]; then
  echo "Completions already installed"
else
  echo "Installing tmux completions"
  wget -qO "$completions_path" https://raw.githubusercontent.com/imomaliev/tmux-bash-completion/master/completions/tmux
  echo "Completions saved to $completions_path"
fi
