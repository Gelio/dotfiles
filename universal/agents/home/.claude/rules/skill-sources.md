# Where a skill comes from

- Before editing a skill, resolve its link
  (`readlink -f ~/.claude/skills/<name>`) to see who owns it:
  - Under `~/projects/dotfiles/universal/agents/home/.agents/skills/` and listed
    in the dotfiles' `universal/agents/vendored-skills.json`: vendored from
    upstream. `update-skills.py` overwrites the folder with upstream's copy.
  - Under that folder and not in the manifest: authored. Edit it there.
  - Plugin skills under `~/.claude/plugins/`: third-party, overwritten by the
    next plugin update.
- Don't edit a vendored or plugin skill in place. Suggest an option to the user
  instead: fork it (drop its manifest entry, keep the upstream credit in its
  `metadata.credits`), send the change upstream, or leave it.
