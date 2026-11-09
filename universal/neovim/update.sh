#!/usr/bin/env bash
# Bumps neovim-commit to the tip of Neovim's master (or to the given full SHA),
# builds it with install.sh, and prints the commits since the previous pin along
# with a prompt that asks an agent for their highlights.
#
# Usage: update.sh [-c | --clean] [COMMIT]
#   -c, --clean  Run `make distclean` before building
set -euo pipefail

# Allows running the script from any directory
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
pushd "$script_dir" >/dev/null

neovim_dir="$HOME/.local/neovim"
old_commit="$(<neovim-commit)"
new_commit=""
clean_flag=""

while (($#)); do
  case "$1" in
  -c | --clean)
    clean_flag="--clean"
    ;;

  *)
    new_commit="$1"
    ;;
  esac
  shift
done

if [[ -z "$new_commit" ]]; then
  new_commit="$(git ls-remote https://github.com/neovim/neovim.git refs/heads/master | cut -f1)"
fi

if [[ ! "$new_commit" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Expected a full commit SHA, got '$new_commit'" >&2
  exit 1
fi

if [[ "$new_commit" == "$old_commit" ]]; then
  echo "* neovim-commit is already at $old_commit"
  exit 0
fi

function restore_pin {
  echo "$old_commit" >neovim-commit
  echo "* Update failed, neovim-commit is back at $old_commit" >&2
}

echo "* Updating neovim from $old_commit to $new_commit"
# install.sh builds whatever neovim-commit holds. The pin only stays bumped if
# that build succeeds.
trap restore_pin EXIT
echo "$new_commit" >neovim-commit
./install.sh ${clean_flag:+"$clean_flag"}
trap - EXIT

echo
echo "* Commits in this update"
git --no-pager -C "$neovim_dir" log --oneline "$old_commit..$new_commit"

cat <<EOF

* Prompt for an agent

Give me the highlights of this Neovim update. List the commits with
\`git -C $neovim_dir log --oneline $old_commit..$new_commit\`
and use \`git -C $neovim_dir show <commit>\` when a subject doesn't say enough.
Group them into breaking changes, new features, and notable fixes. Leave out
refactors, tests, CI, and vim-patch commits without a user-visible effect. Call
out anything that affects my config in $script_dir/config/nvim.

* neovim-commit now holds the new commit. Commit it and open a PR, so that CI checks that the config starts on it.
EOF
