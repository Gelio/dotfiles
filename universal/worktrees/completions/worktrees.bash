# Bash completion for the `worktrees` CLI.
#
# Hybrid: subcommands and flags are completed statically here (instant, no Node
# startup); only the dynamic value slots — `setup --from <ref>` and
# `teardown <name>` — shell out to `worktrees __complete`, the single source of
# truth for those candidates.
#
# Installed by install.sh as ~/.local/share/bash-completion/completions/worktrees
# (bash-completion's standard per-command autoload dir).

_worktrees() {
  local cur prev cword
  if declare -F _init_completion >/dev/null 2>&1; then
    _init_completion || return
  else
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    cword=$COMP_CWORD
  fi

  if [[ $cword -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "setup teardown list sync init config-path" -- "$cur") )
    return
  fi

  case "${COMP_WORDS[1]}" in
    setup)
      if [[ "$prev" == "--from" ]]; then
        COMPREPLY=( $(compgen -W "$(worktrees __complete setup --from '' 2>/dev/null)" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--from" -- "$cur") )
      fi
      ;;
    teardown)
      COMPREPLY=( $(compgen -W "$(worktrees __complete teardown '' 2>/dev/null)" -- "$cur") )
      ;;
    list)
      COMPREPLY=( $(compgen -W "--all" -- "$cur") )
      ;;
    init)
      COMPREPLY=( $(compgen -W "--in-repo" -- "$cur") )
      ;;
  esac
}

complete -F _worktrees worktrees
