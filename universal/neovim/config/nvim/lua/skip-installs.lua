-- Set NVIM_SKIP_INSTALLS=1 to start without downloading or building anything:
-- no Mason packages, no Treesitter parsers and no plugin builds. The pull
-- request CI job uses it to stay fast. The daily full install job leaves it
-- unset.
return vim.env.NVIM_SKIP_INSTALLS == "1"
