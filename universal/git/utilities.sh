#!/bin/bash
set -euo pipefail

# https://github.com/epage/git-stack
# https://github.com/Wilfred/difftastic
# https://github.com/tummychow/git-absorb
cargo binstall gitui git-stack difftastic git-absorb

# https://github.com/arxanas/git-branchless
cargo binstall --locked git-branchless

# https://github.com/jesseduffield/lazygit
go install github.com/jesseduffield/lazygit@latest
