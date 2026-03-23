#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract values
model_id=$(echo "$input" | jq -r '.model.id // empty')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // empty')
context_size=$(echo "$input" | jq -r '.context_window.context_window_size // 0')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
current_input=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0')
current_output=$(echo "$input" | jq -r '.context_window.current_usage.output_tokens // 0')
cache_creation=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
cache_read=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')
worktree_name=$(echo "$input" | jq -r '.worktree.name // empty')

# Convert model ID to short name
model_short="Claude"
if [[ "$model_id" == *"opus"* ]]; then
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
    changes=$(cd "$cwd" 2>/dev/null && git -c core.filesystemmonitor=false diff --numstat 2>/dev/null | awk '{added+=$1; removed+=$2} END {if(added+removed>0) printf "+%d -%d", added, removed}')
    if [[ -n "$changes" ]]; then
        git_changes=" $changes"
    fi
fi

# Worktree indicator
worktree_info=""
if [[ -n "$worktree_name" ]]; then
    worktree_info=" • 🌿 $worktree_name"
fi

# Shorten directory path
short_cwd="$cwd"
if [[ "$cwd" == "$HOME"* ]]; then
    short_cwd="~${cwd#$HOME}"
fi

# ANSI colors
GREEN='\033[38;5;108m'
BLUE='\033[38;5;67m'
YELLOW='\033[33m'
RED='\033[31m'
RESET='\033[0m'

# Context usage (used/total + percentage + auto-compact estimate)
current_used=$((current_input + current_output + cache_creation + cache_read))
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
            ctx_color="$BLUE"
        elif [[ $remaining_int -ge 20 ]]; then
            ctx_color="$YELLOW"
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
    parts+=("[$model_short] $git_branch$git_changes")
else
    parts+=("[$model_short]")
fi

# Worktree (if present)
if [[ -n "$worktree_info" ]]; then
    parts[0]="${parts[0]}$worktree_info"
fi

# Current directory
parts+=("$short_cwd")

# Context usage
if [[ -n "$token_display" ]]; then
    parts+=("$token_display")
fi

# Elapsed time
if [[ -n "$elapsed_display" ]]; then
    parts+=("$elapsed_display")
fi

# Join with bullet separator
output=""
for i in "${!parts[@]}"; do
    if [[ $i -eq 0 ]]; then
        output="${parts[$i]}"
    else
        output="$output • ${parts[$i]}"
    fi
done

printf '%b\n' "$output"
