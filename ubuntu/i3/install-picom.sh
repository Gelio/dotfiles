#!/usr/bin/env bash

set -euo pipefail

# https://github.com/yshui/picom#build

sudo apt install \
  libconfig-dev \
  libdbus-1-dev \
  libev-dev \
  libevdev-dev \
  libgl1-mesa-dev \
  libpcre2-dev \
  libpcre3-dev \
  libpixman-1-dev \
  libx11-xcb-dev \
  libxcb-composite0-dev \
  libxcb-damage0-dev \
  libxcb-dpms0-dev \
  libxcb-glx0-dev \
  libxcb-image0-dev \
  libxcb-present-dev \
  libxcb-randr0-dev \
  libxcb-render-util0-dev \
  libxcb-render0-dev \
  libxcb-shape0-dev \
  libxcb-xfixes0-dev \
  libxcb-xinerama0-dev \
  libxcb1-dev \
  libxext-dev \
  uthash-dev

pip3 install --user meson

cd ~/.local
if [[ -d picom ]]; then
  cd picom
  git pull
  # NOTE: cleans previous build artifacts. Not doing so sometimes causes
  # Meson and Ninja to be confused.
  git clean -xdf
else
  git clone https://github.com/yshui/picom.git
  cd picom
fi

git submodule update --init --recursive
meson --buildtype=release . build
ninja -C build
[[ ! -f ~/.local/bin/picom ]] && ln -s "$PWD/build/src/picom" ~/.local/bin/picom || echo "Symlink already exists, skipping"
