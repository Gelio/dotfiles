#!/usr/bin/env bash

set -euo pipefail

# Build redshift from source due to a bug that prevents loading the config
# when using a prebuilt binary

# https://github.com/jonls/redshift/blob/master/CONTRIBUTING.md#building-from-git-clone
sudo apt install autopoint intltool libdrm-dev libxcb1-dev libxcb-randr0-dev \
  libx11-dev libxxf86vm-dev libglib2.0-dev python3 libtool

cd ~/.local
[[ ! -d redshift ]] && git clone https://github.com/jonls/redshift.git
cd redshift
./bootstrap
./configure --enable-{drm,randr,vidmode,geoclue2,gui,ubuntu,apparmor}
make
sudo make install
