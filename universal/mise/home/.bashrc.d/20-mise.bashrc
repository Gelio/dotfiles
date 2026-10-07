# bootstrap.sh installs mise to ~/.local/bin, which ~/.profile adds to PATH only after ~/.bashrc
command -v mise >/dev/null || PATH="$HOME/.local/bin:$PATH"
eval "$(mise activate bash)"
source <(mise completion bash)

eval "$(fzf --bash)"

# vim: ft=sh
