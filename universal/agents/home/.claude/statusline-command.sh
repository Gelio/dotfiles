#!/usr/bin/env bash
# Claude Code status line: model, effort, directory and git branch, context,
# plan usage limits and session time.

input=$(cat)

# Save plan usage limits (% used and reset time per window) so agents can
# check how close they are to a limit. Every open session renders its own
# copy of the limits, as of its last API response, so stamp them with the
# transcript's last write and keep whichever copy is newest.
limits_file=~/.cache/claude-rate-limits.json
limits_transcript=$(jq -r '.transcript_path // empty' <<<"$input")
if [[ "$(uname)" == "Darwin" ]]; then
    limits_epoch=$(stat -f %m "$limits_transcript" 2>/dev/null)
else
    limits_epoch=$(stat -c %Y "$limits_transcript" 2>/dev/null)
fi
cached_epoch=$(jq -r '.updated_at_epoch // 0' "$limits_file" 2>/dev/null)
if [[ -n "$limits_epoch" ]] && jq -e '.rate_limits' <<<"$input" >/dev/null 2>&1 \
    && [[ "$limits_epoch" -ge "${cached_epoch:-0}" ]]; then
    jq -c --argjson at "$limits_epoch" '{updated_at: ($at | todate), updated_at_epoch: $at, rate_limits: (.rate_limits | map_values(if .resets_at then .resets_at_iso = (.resets_at | todate) else . end))}' \
        <<<"$input" > "$limits_file.$$" 2>/dev/null && mv "$limits_file.$$" "$limits_file"
fi

# One value per line, so empty values keep their place.
{
    read -r model
    read -r effort
    read -r cwd
    read -r ctx_used
    read -r ctx_size
    read -r five_hour
    read -r seven_day
    read -r duration_ms
} < <(jq -r '
    .model.display_name // .model.id // "",
    .effort.level // "",
    .workspace.current_dir // .cwd // "",
    .context_window.total_input_tokens // "",
    .context_window.context_window_size // "",
    (.rate_limits.five_hour.used_percentage // "" | if . == "" then . else floor end),
    (.rate_limits.seven_day.used_percentage // "" | if . == "" then . else floor end),
    (.cost.total_duration_ms // "" | if . == "" then . else floor end)
' <<<"$input")

reset=$'\e[0m'
# A mid gray rather than the faint attribute, which some colorschemes make
# hard to read.
dim=$'\e[38;5;247m'
red=$'\e[31m'
green=$'\e[32m'
yellow=$'\e[33m'
blue=$'\e[34m'
magenta=$'\e[35m'
cyan=$'\e[36m'
orange=$'\e[38;5;208m'
bold_red=$'\e[1;31m'

path_max=40

# Shorten a path to path_max characters: cut parent folders to 2 characters
# from the left until it fits, then cut the last folder from its start.
shorten_path() {
    local path=$1
    [[ "$path" == "$HOME" || "$path" == "$HOME"/* ]] && path="~${path#"$HOME"}"
    if (( ${#path} <= path_max )); then
        printf '%s' "$path"
        return
    fi

    local -a parts
    IFS=/ read -ra parts <<<"$path"
    local last=$(( ${#parts[@]} - 1 )) i joined
    for (( i = 0; i < last; i++ )); do
        [[ "${parts[i]}" == "~" ]] && continue
        parts[i]=${parts[i]:0:2}
        joined=$(IFS=/; printf '%s' "${parts[*]}")
        if (( ${#joined} <= path_max )); then
            printf '%s' "$joined"
            return
        fi
    done

    # Keep the parents and as much of the end of the last folder as fits.
    local prefix=""
    (( last > 0 )) && prefix="$(IFS=/; printf '%s' "${parts[*]:0:last}")/"
    local room=$(( path_max - ${#prefix} - 1 ))
    if (( room < 4 )); then
        # The parents alone fill the limit, so show only the last folder.
        prefix=""
        room=$(( path_max - 1 ))
    fi
    printf '%s…%s' "$prefix" "${parts[last]: -room}"
}

usage_color() {
    if (( $1 >= 80 )); then printf '%s' "$red"
    elif (( $1 >= 50 )); then printf '%s' "$yellow"
    else printf '%s' "$green"
    fi
}

# Bands by token count keep long conversations under about 200k tokens even
# on a 1M window; on a small window, 80% full is red too.
context_color() {
    local used=$1 size=$2 band=0
    if (( used >= 250000 || used * 100 >= size * 80 )); then band=3
    elif (( used >= 200000 )); then band=2
    elif (( used >= 120000 )); then band=1
    fi
    case $band in
        0) printf '%s' "$green" ;;
        1) printf '%s' "$yellow" ;;
        2) printf '%s' "$orange" ;;
        3) printf '%s' "$red" ;;
    esac
}

sections=()

model_section=""
if [[ -n "$model" ]]; then
    case "$model" in
        *[Oo]pus*) model_color=$magenta ;;
        *[Ss]onnet*) model_color=$blue ;;
        *[Hh]aiku*) model_color=$green ;;
        *[Ff]able*) model_color=$cyan ;;
        *) model_color="" ;;
    esac
    model_section="${model_color}${model}${reset}"
fi
if [[ -n "$effort" ]]; then
    case "$effort" in
        low) effort_color=$dim ;;
        high) effort_color=$yellow ;;
        xhigh | max) effort_color=$bold_red ;;
        *) effort_color="" ;;
    esac
    model_section+="${model_section:+ }${effort_color}${effort}${reset}"
fi
[[ -n "$model_section" ]] && sections+=("$model_section")

if [[ -n "$cwd" ]]; then
    cwd_section="${cyan}$(shorten_path "$cwd")${reset}"
    # The branch, or the short commit when HEAD is detached. --no-optional-locks
    # keeps the status line from contending with git commands in the session.
    branch=$(git -C "$cwd" --no-optional-locks branch --show-current 2>/dev/null)
    [[ -z "$branch" ]] && branch=$(git -C "$cwd" --no-optional-locks rev-parse --short HEAD 2>/dev/null)
    [[ -n "$branch" ]] && cwd_section+=" ${magenta}${branch}${reset}"
    sections+=("$cwd_section")
fi

if [[ -n "$ctx_used" && -n "$ctx_size" ]] && (( ctx_size > 0 )); then
    ctx_pct=$(( ctx_used * 100 / ctx_size ))
    sections+=("$(context_color "$ctx_used" "$ctx_size")$(( ctx_used / 1000 ))k/$(( ctx_size / 1000 ))k ${ctx_pct}%${reset}")
fi

limits=()
[[ -n "$five_hour" ]] && limits+=("${dim}5h${reset} $(usage_color "$five_hour")${five_hour}%${reset}")
[[ -n "$seven_day" ]] && limits+=("${dim}7d${reset} $(usage_color "$seven_day")${seven_day}%${reset}")
if (( ${#limits[@]} > 0 )); then
    limits_section=${limits[0]}
    (( ${#limits[@]} > 1 )) && limits_section+=" ${dim}·${reset} ${limits[1]}"
    sections+=("$limits_section")
fi

if [[ -n "$duration_ms" ]]; then
    minutes=$(( duration_ms / 60000 ))
    if (( minutes >= 60 )); then
        elapsed="$(( minutes / 60 ))h$(( minutes % 60 ))m"
    else
        elapsed="${minutes}m"
    fi
    sections+=("${dim}${elapsed}${reset}")
fi

separator=" ${dim}│${reset} "
line=""
for section in "${sections[@]}"; do
    line+="${line:+$separator}${section}"
done
printf '%s\n' "$line"
