# Plan usage limits

- `~/.cache/claude-rate-limits.json` holds the plan's `used_percentage` and `resets_at_iso` per window (`five_hour`, `seven_day`), as of the most recent API response across all sessions (`updated_at`). A window whose reset time has passed starts again at 0%.
- Read it before work that spends a lot of usage: spawning subagents, long autonomous loops, broad reviews. When a window is above 80%, tell the user how much is left and when it resets, and offer a lighter approach (inline instead of subagents, a smaller model, or stopping at a checkpoint) before continuing.
