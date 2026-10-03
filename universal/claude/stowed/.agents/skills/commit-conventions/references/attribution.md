# Agent attribution

Claude Code preserves the existing trailer:

```text
Co-Authored-By: Claude <model-name> <version> <noreply@anthropic.com>
```

Use the active Claude model and version, for example `Claude Opus 4.6`.

Codex uses:

```text
Co-Authored-By: Codex <noreply@openai.com>
```

The Claude and Codex commit hooks validate their own attribution. Fixup,
squash, and `--no-edit` commits retain their existing exceptions.
