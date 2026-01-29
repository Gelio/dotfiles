#!/bin/bash
set -euo pipefail

# A viewer for git diffs
# If rust is not installed, use another installation option https://github.com/dandavison/delta#installation
cargo binstall git-delta
