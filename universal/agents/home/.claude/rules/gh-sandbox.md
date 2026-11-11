# gh under the sandbox

- The sandbox denies reads of `~/.config/gh/hosts.yml`, which holds the gh
  login. `gh` and `gh *` are excluded from the sandbox, but the exclusion only
  matches a command that starts with `gh`. Anything around it (`cd … &&`, a
  pipe, `;`, a second command) runs the whole command sandboxed, and gh fails
  with `failed to read configuration: open …/gh/hosts.yml`.
- So run each `gh` call as its own single-line Bash command:
  - Pass long text with `--body-file <file>` (write the file first, in a
    separate call), not a multi-line `--body`.
  - Filter output with `--jq` (and `--template`) instead of piping to `jq`. For
    a file's contents, use
    `gh api -H 'Accept: application/vnd.github.raw' repos/<owner>/<repo>/contents/<path>`
    instead of piping to `base64 -d`.
  - Use `--repo <owner>/<repo>` instead of `cd` into a clone.
- On the `hosts.yml` error, rerun the call on its own, as above. Don't hand the
  command to the user, and don't suggest loosening `denyRead`: keeping the login
  unreadable to sandboxed commands is intended.
