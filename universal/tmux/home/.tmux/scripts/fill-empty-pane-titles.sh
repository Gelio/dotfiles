#!/usr/bin/env bash
#
# Fill in any *empty* pane titles with the host name (tmux's own default
# title) so tmux-resurrect saves a well-formed snapshot.
#
# Why this exists
# ---------------
# resurrect's save format is "...#{pane_title}<TAB>:#{pane_current_path}..."
# (see ~/.tmux/plugins/tmux-resurrect/scripts/save.sh). When a pane's title
# is empty, that line contains two adjacent tabs. save.sh parses it with
# `while IFS=$'\t' read ... pane_title dir ...`, and because tab is an
# IFS-whitespace character, bash `read` collapses the adjacent tabs into a
# single delimiter. The empty title field vanishes, every later field shifts
# left, and the saved `dir` column ends up holding a bogus value (e.g. "1").
# On restore, `tmux new-window -c "$dir"` then gets an empty directory and the
# pane silently reopens in $HOME.
#
# A pane title goes empty when a program emits a title-reset escape
# (ESC ] 2 ; ESC \) and nothing sets a new one afterwards (common when a TUI
# exits back to an idle shell). It is invisible here because set-titles is off.
#
# Fix: keep titles non-empty. We ride continuum's status-line redraw timer
# (status-interval, 5s) rather than a tmux event hook, because continuum saves
# on a timer for *unfocused* panes too — an event-driven hook would leave a
# gap. We only ever fill blanks, so a program's own title is never overridden.

set -euo pipefail

# Emit the pane id for every pane whose title is empty, nothing otherwise.
# In the common case (no empty titles) this single list-panes call is the only
# work done: the loop body never runs and the host name is never computed.
host=""
tmux list-panes -a -F '#{?#{==:#{pane_title},},#{pane_id},}' |
	while read -r pane_id; do
		if [ -n "$pane_id" ]; then
			# tmux's default pane title is the short host name; matching it
			# keeps a filled pane indistinguishable from a fresh one. Computed
			# lazily (at most once) only when there's actually a blank to fill.
			[ -n "$host" ] || host="$(tmux display-message -p '#{host_short}')"
			tmux select-pane -t "$pane_id" -T "$host"
		fi
	done

# Print nothing: this runs as a status-right "#()" component and must stay
# visually empty.
exit 0
