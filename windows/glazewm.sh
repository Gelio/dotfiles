#!/usr/bin/env bash
set -euo pipefail

winget.exe install GlazeWM --exact
./config.sh push glzr
