local M = {}

local utils = require("lsp.utils")

---@type string[]
local filetypes = vim.lsp.config.ts_ls.filetypes
assert(#filetypes > 0, "ts_ls filetypes must be defined")
table.insert(filetypes, "vue")

M.config = vim.tbl_extend("force", utils.base_config, {
	filetypes = filetypes,

	settings = {
		tsserver_plugins = {
			"@vue/typescript-plugin",
		},
	},
})

M.setup = function(config)
	if config == nil then
		config = M.config
	end

	-- WORKAROUND: the `setup` expects LSP config to be passed in `opts.config`,
	-- not directly.
	-- See https://github.com/pmizio/typescript-tools.nvim/issues/376
	local opts = {
		settings = config.settigns,
		config = config,
	}

	require("typescript-tools").setup(opts)
end

return M
