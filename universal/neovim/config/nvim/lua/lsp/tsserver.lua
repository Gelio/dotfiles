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

	require("typescript-tools").setup(config)
end

return M
