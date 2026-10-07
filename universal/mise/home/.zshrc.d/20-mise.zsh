# bootstrap.sh installs mise to ~/.local/bin, which is not always on PATH yet here
command -v mise >/dev/null || PATH="$HOME/.local/bin:$PATH"
eval "$(mise activate zsh)"
source <(mise completion zsh)

eval "$(fzf --zsh)"

# vim: ft=sh
