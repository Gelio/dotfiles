#!/usr/bin/env bash
set -euo pipefail

winget.exe install Microsoft.PowerToys --exact
./config.sh push keyboard
