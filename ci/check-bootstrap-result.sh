#!/usr/bin/env bash
# Checks what a real `bootstrap.sh --only dotfiles` left behind: the group config
# files mise loaded, the links on disk, and that nothing dangles or was moved
# aside. Compares files on disk with the repo, as mise's own status alone could
# agree with itself.
#
# usage: check-bootstrap-result.sh "<space-separated enabled groups>"
#
# NOTE: runs on macOS bash 3.2 too
set -euo pipefail

enabled=" ${1?usage: check-bootstrap-result.sh \"<enabled groups>\"} "
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." &>/dev/null && pwd)"
config_dir="$repo/universal/mise/config"
failed=0

function problem {
  echo "FAIL: $*" >&2
  failed=1
}

function jq_tool {
  mise x jq -- jq "$@"
}

# Outside the repo, for the same reason bootstrap.sh is
cd "$HOME"

[[ "$HOME/.config/mise" -ef "$config_dir" ]] || problem "$HOME/.config/mise doesn't link to $config_dir"

# The enabled groups, and only those, are loaded
loaded="$(mise config ls --json | jq_tool -r '.[].path')"
for file in "$config_dir"/config.*.toml; do
  group="$(basename "$file" .toml)"
  group="${group#config.}"
  [[ "$group" == local ]] && continue
  if grep -q "/config\.$group\.toml$" <<<"$loaded"; then
    [[ "$enabled" == *" $group "* ]] || problem "group $group is loaded but shouldn't be"
  else
    [[ "$enabled" != *" $group "* ]] || problem "group $group should be loaded but isn't"
  fi
done

status="$(mise dot status --json)"

not_applied="$(jq_tool -r '(.files + .edits)[] | select(.state != "applied") | "\(.target // .path) (\(.state))"' <<<"$status")"
[[ -z "$not_applied" ]] || problem "entries not applied:"$'\n'"$not_applied"

checked=0
while IFS=$'\t' read -r mode target source; do
  target="${target/#\~/$HOME}"
  case "$mode" in
  symlink)
    checked=$((checked + 1))
    [[ -L "$target" && "$target" -ef "$source" ]] || problem "$target doesn't link to $source"
    ;;
  symlink-each)
    while IFS= read -r file; do
      checked=$((checked + 1))
      # A file under a directory linked as a whole resolves through that link
      [[ "$target/${file#"$source"/}" -ef "$file" ]] || problem "$target/${file#"$source"/} doesn't link to $file"
    done < <(find "$source" \( -type f -o -type l \))
    ;;
  esac
done < <(jq_tool -r '.files[] | [.mode, .target, .origin.source] | @tsv' <<<"$status")
((checked > 0)) || problem "no dotfile links to check"

# The checkout, the runner and mise's own installs aren't ours to check
while IFS= read -r path; do
  if [[ "$path" == *.pre-mise-* ]]; then
    problem "moved aside: $path"
  elif [[ -L "$path" && ! -e "$path" ]]; then
    problem "dangling link: $path -> $(readlink "$path")"
  fi
done < <(find "$HOME" \
  \( -path "$HOME/work" -o -path "$HOME/runners" -o -path "$HOME/actions-runner" \
  -o -path "$HOME/Library" -o -path "$HOME/.local/share/mise" -o -path "$HOME/.cache" \) -prune \
  -o \( -type l -o -name '*.pre-mise-*' \) -print)

if ((failed)); then
  exit 1
fi
echo "Checked $checked links; groups:$enabled"
