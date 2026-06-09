return {
	-- NOTE: ruff handles linting, code actions and import organizing. Hover is
	-- disabled so basedpyright (the type checker) is the single source for hover
	-- docs and type information.
	-- https://docs.astral.sh/ruff/editors/setup/#neovim
	on_attach = function(client)
		client.server_capabilities.hoverProvider = false
	end,
}
