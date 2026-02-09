#!/usr/bin/env bash
set -euo pipefail

# Allows running the script from any directory
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
pushd "$script_dir" >/dev/null

clean_before_build=false
skip_pull=false

while :; do
  case "${1:-""}" in
  -c | --clean)
    clean_before_build=true
    shift
    ;;

  --skip-pull)
    skip_pull=true
    shift
    ;;

  *)
    break
    ;;
  esac

done

function main {
  pushd ~/.local >/dev/null
  if [[ -d neovim ]]; then
    cd neovim
    echo "* neovim repository found at $PWD"

    if [[ "$skip_pull" == false ]]; then

      echo "  Pulling latest changes..."
      # Pulling fails most likely when a hash is checked out, not a branch.
      # This is normal when there are breaking changes on master and a previous
      # commit is used to build neovim.
      git pull || echo "Pulling latest changes failed. Continuing anyway"
    else
      echo "  Skipped pulling latest changes"
    fi

    # Sometimes there are ninja build permissions errors because some files
    # are owned by root instead of the current user.
    # [3/3] cd /home/voreny/.local/neovim/.deps && /usr/bin/cmake -E touch .third-party
    # ninja  -C build
    # ninja: Entering directory `build'
    # ninja: error: opening build log: Permission denied
    # make: *** [Makefile:92: nvim] Error 1
    sudo chown -R "$USER" .
  else
    echo "* neovim repository not found in $HOME/.local/neovim, cloning..."
    git clone git@github.com:neovim/neovim.git
    cd neovim

    echo "* Installing build prerequisites"
    install_build_prerequisites

    echo "* Installing runtime prerequisites"
    install_runtime_prerequisites
  fi

  echo "* Building neovim"
  build_neovim
  nvim -v
  popd >/dev/null

  echo "* Stowing config files"
  ./stow.sh
  echo "* Done"
}

function install_runtime_prerequisites {
  # Install python3 provider for neovim
  # See https://neovim.io/doc/user/provider.html
  python3 -m pip install --user --upgrade pynvim

  if [[ "$(uname)" != "Darwin" ]]; then
    # xsel for clipboard support
    # g++ for compiling Treesitter parsers
    sudo apt install xsel g++
  fi
}

function install_build_prerequisites {
  if [[ "$(uname)" == "Darwin" ]]; then
    # https://github.com/neovim/neovim/wiki/Building-Neovim#macos--homebrew
    brew install ninja cmake gettext curl
  else
    # https://github.com/neovim/neovim/wiki/Building-Neovim#ubuntu--debian
    sudo apt-get install ninja-build gettext libtool libtool-bin autoconf automake cmake g++ pkg-config unzip curl doxygen
  fi
}

function build_neovim {
  # https://github.com/neovim/neovim/wiki/Building-Neovim#building
  if [[ "$clean_before_build" == true ]]; then
    make distclean
  fi
  echo "* Running build"
  make CMAKE_BUILD_TYPE=RelWithDebInfo
  echo "* Installing"
  # Pass the PATH to sudo so it can find cmake/ninja if needed during install
  sudo env "PATH=$PATH" make install
}

main
