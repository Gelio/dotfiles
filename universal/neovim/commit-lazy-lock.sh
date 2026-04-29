#!/usr/bin/env bash
set -euo pipefail

lazy_lock_path=./config/nvim/lazy-lock.json

diff_staged=""

if [[ -n "$(git diff --staged -- "$lazy_lock_path")" ]]; then
  diff_staged="--staged"
  echo "lazy-lock.json is staged. Looking only at staged changes"
fi

modified_packages=$(
  git diff --unified=0 $diff_staged -- "$lazy_lock_path" |
    grep "^\\+ " |
    sed -E "s/^\\+[[:space:]]+\"([^\"]+)\":.*/\1/" || true
)

if [[ -z "$modified_packages" ]]; then
  echo "Nothing to commit"
  exit 0
fi

formatted_packages=$(awk '{print "* " $0}' <<<"$modified_packages")

commit_message="chore(nvim): update lazy-lock.json

Updated packages:
$formatted_packages"

if [[ -z $diff_staged ]]; then
  # Only add the file if it has not been staged earlier
  git add "$lazy_lock_path"
fi
git commit -m "$commit_message"
