#!/usr/bin/env bash
set -euo pipefail

cargo binstall --git https://github.com/rtk-ai/rtk rtk
rtk init -g
