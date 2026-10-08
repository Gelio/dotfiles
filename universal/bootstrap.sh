#!/usr/bin/env bash
set -euo pipefail

# Sets up mise-managed tools and their dotfiles on this machine.
# Extra arguments are passed to `mise bootstrap`, e.g. --dry-run.
universal_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
config_dir="$universal_dir/mise/config"
mise_link="$HOME/.config/mise"

# Pinned mise release, installed only when mise is missing. Afterwards
# `mise self-update` upgrades it. Hashes come from the release's SHASUMS256.txt:
# https://github.com/jdx/mise/releases/download/v<version>/SHASUMS256.txt
mise_version="2026.10.3"

function install_mise {
  local os arch platform expected_sha actual_sha download
  case "$(uname -s)" in
  Linux) os=linux ;;
  Darwin) os=macos ;;
  *)
    echo "> Unsupported OS: $(uname -s)" >&2
    return 1
    ;;
  esac
  case "$(uname -m)" in
  x86_64 | amd64) arch=x64 ;;
  aarch64 | arm64) arch=arm64 ;;
  *)
    echo "> Unsupported CPU: $(uname -m)" >&2
    return 1
    ;;
  esac
  platform="$os-$arch"
  case "$platform" in
  linux-x64) expected_sha=8d48bc510b7d844fad0bc7156c0855c2a1e7230c51e498a7f6b63b021f8b57c5 ;;
  linux-arm64) expected_sha=357260e28904569a6e7124d33b65cef6d043846c07bb8f4906ddf22cc353d61d ;;
  macos-x64) expected_sha=38cdd1d904b25e66ec2fff3b5c88930853ab929b63e72c70e77198f82d6ac144 ;;
  macos-arm64) expected_sha=0999bd4943523ccdbd149b5ad4080281536801b3f6406ac4495699bd0310969c ;;
  esac

  download="$(mktemp)"
  curl -fsSL -o "$download" \
    "https://github.com/jdx/mise/releases/download/v${mise_version}/mise-v${mise_version}-${platform}"
  if command -v sha256sum >/dev/null; then
    actual_sha="$(sha256sum "$download" | cut -d' ' -f1)"
  else
    actual_sha="$(shasum -a 256 "$download" | cut -d' ' -f1)"
  fi
  if [[ "$actual_sha" != "$expected_sha" ]]; then
    rm -f "$download"
    echo "> SHA-256 mismatch for mise $mise_version $platform" >&2
    echo ">   expected $expected_sha" >&2
    echo ">   got      $actual_sha" >&2
    return 1
  fi

  mkdir -p "$HOME/.local/bin"
  chmod +x "$download"
  mv "$download" "$HOME/.local/bin/mise"
  echo "> Installed mise $mise_version to ~/.local/bin/mise"
}

if ! command -v mise >/dev/null; then
  install_mise
  export PATH="$HOME/.local/bin:$PATH"
fi

# [dotfile_groups] needs at least the pinned version.
installed_version="$(mise --version | cut -d' ' -f1)"
if [[ "$(printf '%s\n' "$mise_version" "$installed_version" | sort -V | head -1)" != "$mise_version" ]]; then
  echo "> mise $installed_version is older than $mise_version. Run 'mise self-update' and re-run." >&2
  exit 1
fi

mkdir -p "$HOME/.config"
if [[ -L "$mise_link" ]]; then
  ln -sfn "$config_dir" "$mise_link"
elif [[ -e "$mise_link" ]]; then
  echo "> $mise_link exists and is not a symlink. Move it away and re-run." >&2
  exit 1
else
  ln -s "$config_dir" "$mise_link"
fi
echo "> $mise_link -> $config_dir"

# dotfile group roots are relative to dotfiles.root, and the repo path differs
# between machines, so it lives in a gitignored per-machine file.
local_config="$config_dir/config.local.toml"
if [[ ! -f "$local_config" ]]; then
  printf '[settings]\ndotfiles.root = "%s"\n' "$universal_dir" >"$local_config"
  echo "> Created $local_config"
fi

miserc="$config_dir/miserc.toml"
if [[ ! -f "$miserc" ]]; then
  cat >"$miserc" <<'EOF'
# Optional tool groups for this machine. Each name loads config.<name>.toml.
# Available: git, fs, sys, lang, ai, work
env = []
EOF
  echo "> Created $miserc. Edit it to enable optional groups, then re-run."
fi

# mise refuses to replace what is in the way of a directory it links as a whole:
# a real directory of per-file links from older setups, a stow link, or a
# default config the tool wrote itself (atuin's shell hook does that at every
# prompt). Move these aside right before linking, so nothing recreates them in
# between. `mise x` installs jq first on a new machine.
dry_run=false
for arg in "$@"; do
  [[ "$arg" == --dry-run || "$arg" == -n ]] && dry_run=true
done
backup_suffix="pre-mise-$(date +%Y%m%d%H%M%S)"
mise dot status --json |
  mise x jq -- jq -r '.files[] | select(.mode == "symlink" and .state == "differs") | .target' |
  while IFS= read -r target; do
    target="${target/#\~/$HOME}"
    if $dry_run; then
      echo "> Would move $target to $target.$backup_suffix"
    else
      mv "$target" "$target.$backup_suffix"
      echo "> Moved $target to $target.$backup_suffix. Delete it once you've checked it"
    fi
  done

mise bootstrap --only dotfiles,tools "$@"
