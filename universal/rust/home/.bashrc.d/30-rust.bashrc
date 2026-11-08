#!/usr/bin/env bash

# shellcheck disable=SC1090 # generated when the shell starts, nothing to follow
source <(rustup completions bash rustup)
# shellcheck disable=SC1090 # generated when the shell starts, nothing to follow
source <(rustup completions bash cargo)
