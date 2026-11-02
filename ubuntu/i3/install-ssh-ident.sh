#!/usr/bin/env bash

set -euo pipefail

sudo apt install python-is-python3

cd ~/.local
[ ! -d ssh-ident ] && git clone https://github.com/ccontavalli/ssh-ident.git
cd ssh-ident
ln -s "$PWD/ssh-ident" ~/.local/bin/ssh
./stow.sh
