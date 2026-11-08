#!/usr/bin/env bash

set -euo pipefail

# https://github.com/luarocks/luarocks/wiki/Installation-instructions-for-Unix

sudo apt install build-essential libreadline-dev

# Install lua
LUA_VERSION=5.3.5
cd ~/.local
curl -R -O http://www.lua.org/ftp/lua-$LUA_VERSION.tar.gz
tar -zxf lua-$LUA_VERSION.tar.gz
rm lua-$LUA_VERSION.tar.gz
cd lua-$LUA_VERSION
make linux test
sudo make install

# Install Luarocks
LUAROCKS_VERSION=3.3.1
cd ~/.local
wget https://luarocks.org/releases/luarocks-$LUAROCKS_VERSION.tar.gz
tar zxpf luarocks-$LUAROCKS_VERSION.tar.gz
rm luarocks-$LUAROCKS_VERSION.tar.gz
cd luarocks-$LUAROCKS_VERSION
./configure --with-lua-include=/usr/local/include
make
sudo make install

# shellcheck disable=SC2016 # written to .bashrc unexpanded, on purpose
echo 'export PATH="$PATH:~/.luarocks/bin"' >>~/.bashrc
