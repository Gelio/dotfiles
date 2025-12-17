#!/usr/bin/env bash
set -eou pipefail

app_name=Linearmouse
config_location=.config/linearmouse/linearmouse.json
config_path=~/$config_location

if [ ! -f "$config_path" ]; then
  echo "$app_name config not found at $config_path"
  exit 1
fi

stowed_config_path=$(realpath ./stowed/$config_location)

# NOTE: `&& true` is used to prevent the script from exiting due to "set -e"
diff "$config_path" "$stowed_config_path" >/dev/null && true
error_code=$?

if [ $error_code -eq 0 ]; then
  echo "$app_name config is already up to date"
  exit 0
fi

cp "$config_path" "$stowed_config_path"
echo "$app_name config copied to $stowed_config_path"
rm "$config_path"
ln -s "$stowed_config_path" "$config_path"
