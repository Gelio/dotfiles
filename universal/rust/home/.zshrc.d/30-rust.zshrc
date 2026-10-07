#!/usr/bin/env zsh

source <(rustup completions zsh rustup)
# Cargo completions cannot be sourced inline. They must come from a regular file.
[[ -f ~/.zfunc/_cargo ]] || { mkdir -p ~/.zfunc && rustup completions zsh cargo >~/.zfunc/_cargo; }
