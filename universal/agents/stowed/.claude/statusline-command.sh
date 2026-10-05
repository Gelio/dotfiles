#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract values
model_id=$(echo "$input" | jq -r '.model.id // empty')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // empty')
context_size=$(echo "$input" | jq -r '.context_window.context_window_size // 0')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
total_input=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
total_output=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
worktree_name=$(echo "$input" | jq -r '.worktree.name // empty')

# Catppuccin Mocha palette (24-bit)
rgb() { printf '\033[38;2;%d;%d;%dm' "$1" "$2" "$3"; }
GREEN=$(rgb 166 227 161)
RED=$(rgb 243 139 168)
YELLOW=$(rgb 249 226 175)
PEACH=$(rgb 250 179 135)
MAUVE=$(rgb 203 166 247)
BLUE=$(rgb 137 180 250)
LAVENDER=$(rgb 180 190 254)
TEAL=$(rgb 148 226 213)
SKY=$(rgb 137 220 235)
SUBTEXT=$(rgb 166 173 200)
OVERLAY=$(rgb 108 112 134)
BOLD='\033[1m'
RESET='\033[0m'

# Convert model ID to short name
model_short="Claude"
if [[ "$model_id" == *"fable"* ]]; then
    model_short="Fable"
elif [[ "$model_id" == *"opus"* ]]; then
    model_short="Opus"
elif [[ "$model_id" == *"sonnet"* ]]; then
    model_short="Sonnet"
elif [[ "$model_id" == *"haiku"* ]]; then
    model_short="Haiku"
fi

# Git branch (skip optional locks to avoid delays)
git_branch=$(cd "$cwd" 2>/dev/null && git -c core.filesystemmonitor=false rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

# Git line changes (+X -Y format)
git_changes=""
if [[ -n "$git_branch" ]]; then
    read -r added removed < <(cd "$cwd" 2>/dev/null && git -c core.filesystemmonitor=false diff --numstat 2>/dev/null | awk '{added+=$1; removed+=$2} END {printf "%d %d", added, removed}')
    if [[ $((added + removed)) -gt 0 ]]; then
        git_changes=" ${GREEN}+${added}${RESET} ${RED}-${removed}${RESET}"
    fi
fi

# Worktree indicator
worktree_info=""
if [[ -n "$worktree_name" ]]; then
    worktree_info=" ${OVERLAY}•${RESET} ${TEAL}🌿 $worktree_name${RESET}"
fi

# Shorten directory path
short_cwd="$cwd"
if [[ "$cwd" == "$HOME"* ]]; then
    short_cwd="~${cwd#$HOME}"
fi
# Abbreviate all but the last 3 segments to 2 chars (3 for dotdirs)
IFS='/' read -ra segments <<< "$short_cwd"
keep_full=3
for i in "${!segments[@]}"; do
    segment="${segments[$i]}"
    if [[ $i -lt $((${#segments[@]} - keep_full)) && "$segment" != "~" ]]; then
        if [[ "$segment" == .* ]]; then
            segments[$i]="${segment:0:3}"
        else
            segments[$i]="${segment:0:2}"
        fi
    fi
done
short_cwd=$(IFS='/'; echo "${segments[*]}")

# Context usage (used/total + percentage + auto-compact estimate)
current_used=$((total_input + total_output))
token_display=""
if [[ $context_size -gt 0 ]]; then
    # Format as used/total in k
    used_k=$((current_used / 1000))
    total_k=$((context_size / 1000))
    token_display="${used_k}k/${total_k}k"

    if [[ -n "$remaining_pct" ]]; then
        remaining_int=${remaining_pct%.*}
        # Color based on remaining context
        if [[ $remaining_int -ge 60 ]]; then
            ctx_color="$GREEN"
        elif [[ $remaining_int -ge 40 ]]; then
            ctx_color="$YELLOW"
        elif [[ $remaining_int -ge 20 ]]; then
            ctx_color="$PEACH"
        else
            ctx_color="$RED"
        fi

        # Tokens until auto-compact (~83.5% usage, 16.5% buffer)
        compact_threshold=$((context_size * 835 / 1000))
        tokens_until_compact=$((compact_threshold - current_used))
        if [[ $tokens_until_compact -lt 0 ]]; then
            tokens_until_compact=0
        fi
        compact_k=$((tokens_until_compact / 1000))

        # Only show compact info when within 20% of threshold
        compact_20pct=$((compact_threshold * 20 / 100))
        compact_info=""
        if [[ $tokens_until_compact -le $compact_20pct ]]; then
            compact_info=" (compact in ~${compact_k}k)"
        fi

        token_display="${ctx_color}${token_display} ${remaining_int}% left${compact_info}${RESET}"
    fi
fi

# Session cost (from cost.total_cost_usd in statusline JSON — exact, not estimated)
total_cost_usd=$(echo "$input" | jq -r '.cost.total_cost_usd // empty')
session_cost_display=""
if [[ -n "$total_cost_usd" ]] && [[ "$total_cost_usd" != "0" ]]; then
    session_cost_display=$(awk "BEGIN {
        cost = $total_cost_usd;
        if (cost < 0.005) printf \"<\$0.01\"
        else printf \"\$%.2f\", cost
    }")
fi

# Plan usage limits (only present on Pro/Max subscriptions)
# Format one window as "5h 23%", colored by how much is used
format_limit() {
    local label=$1 pct=$2
    [[ -z "$pct" ]] && return
    local used=${pct%.*} color
    if [[ $used -lt 50 ]]; then
        color="$GREEN"
    elif [[ $used -lt 75 ]]; then
        color="$YELLOW"
    elif [[ $used -lt 90 ]]; then
        color="$PEACH"
    else
        color="$RED"
    fi
    printf '%s' "${color}${label} ${used}%${RESET}"
}
IFS=$'\t' read -r five_pct week_pct < <(echo "$input" | jq -r '[.rate_limits.five_hour.used_percentage, .rate_limits.seven_day.used_percentage] | map(. // "" | tostring) | @tsv')
limits_display=""
five_display=$(format_limit 5h "$five_pct")
week_display=$(format_limit 7d "$week_pct")
for limit in "$five_display" "$week_display"; do
    [[ -z "$limit" ]] && continue
    limits_display="${limits_display:+$limits_display ${OVERLAY}·${RESET} }$limit"
done

# Elapsed time (session duration)
# Calculate based on transcript modification time
transcript_path=$(echo "$input" | jq -r '.transcript_path // empty')
elapsed_display=""
if [[ -n "$transcript_path" ]] && [[ -f "$transcript_path" ]]; then
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        transcript_time=$(stat -f %B "$transcript_path" 2>/dev/null || echo "")
    else
        # Linux
        transcript_time=$(stat -c %W "$transcript_path" 2>/dev/null || echo "")
    fi
    
    if [[ -n "$transcript_time" ]]; then
        current_time=$(date +%s)
        elapsed_seconds=$((current_time - transcript_time))
        
        if [[ $elapsed_seconds -ge 3600 ]]; then
            elapsed_hours=$((elapsed_seconds / 3600))
            elapsed_display="${elapsed_hours}h"
        elif [[ $elapsed_seconds -ge 60 ]]; then
            elapsed_minutes=$((elapsed_seconds / 60))
            elapsed_display="${elapsed_minutes}m"
        else
            elapsed_display="${elapsed_seconds}s"
        fi
    fi
fi

# Build output parts
parts=()

# [Model] branch +X -Y
if [[ -n "$git_branch" ]]; then
    parts+=("${BOLD}${MAUVE}[$model_short]${RESET} ${BLUE}$git_branch${RESET}$git_changes")
else
    parts+=("${BOLD}${MAUVE}[$model_short]${RESET}")
fi

# Worktree (if present)
if [[ -n "$worktree_info" ]]; then
    parts[0]="${parts[0]}$worktree_info"
fi

# Current directory
parts+=("${LAVENDER}$short_cwd${RESET}")

# Context usage
if [[ -n "$token_display" ]]; then
    parts+=("$token_display")
fi

# Plan usage limits
if [[ -n "$limits_display" ]]; then
    parts+=("$limits_display")
fi

# Session cost
if [[ -n "$session_cost_display" ]]; then
    parts+=("${SKY}$session_cost_display${RESET}")
fi

# Elapsed time
if [[ -n "$elapsed_display" ]]; then
    parts+=("${SUBTEXT}$elapsed_display${RESET}")
fi

# Join with bullet separator
output=""
for i in "${!parts[@]}"; do
    if [[ $i -eq 0 ]]; then
        output="${parts[$i]}"
    else
        output="$output ${OVERLAY}•${RESET} ${parts[$i]}"
    fi
done

printf '%b\n' "$output"
