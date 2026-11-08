# bootstrap.sh installs mise to ~/.local/bin, which ~/.profile adds to PATH only after ~/.bashrc
command -v mise >/dev/null || PATH="$HOME/.local/bin:$PATH"
eval "$(mise activate bash)"
# shellcheck disable=SC1090 # generated when the shell starts, nothing to follow
source <(mise completion bash)

eval "$(fzf --bash)"

# vim: ft=sh
