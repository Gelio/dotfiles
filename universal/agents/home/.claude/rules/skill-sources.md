# Where a skill comes from

- Before editing a skill, resolve its link
  (`readlink -f ~/.claude/skills/<name>`) to see who owns it:
  - Authored: under `~/projects/dotfiles/universal/agents/home/.agents/skills/`.
    Edit it there.
  - Third-party: installed by `npx skills` and listed in the dotfiles'
    `universal/agents/home/.agents/.skill-lock.json`. Plugin skills under
    `~/.claude/plugins/` are third-party too.
- Don't edit a third-party skill in place: the next `npx skills update` or
  plugin update overwrites it. Suggest an option to the user instead: vendor it
  into `universal/agents/home/.agents/skills/` (drop its lockfile entry, keep
  the upstream credit), send the change upstream, or leave it.
