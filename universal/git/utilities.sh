#!/bin/bash
set -euo pipefail

# UI for git
cargo binstall gitui

# https://github.com/arxanas/git-branchless
cargo binstall --locked git-branchless

# https://github.com/epage/git-stack
cargo binstall git-stack

# https://github.com/Wilfred/difftastic
cargo binstall difftastic

# https://github.com/jesseduffield/lazygit
go install github.com/jesseduffield/lazygit@latest
