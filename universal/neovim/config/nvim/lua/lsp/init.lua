local utils = require("lsp.utils")

local enabled_lsp_clients = {
	"ansiblels",
	"bashls",
	"buf_ls",
	"clangd",
	"css_variables",
	"cssls",
	"docker_language_server",
	"eslint",
	"gopls",
	"jsonls",
	"lua_ls",
	"marksman",
	"prismals",
	"protols",
	"rust_analyzer",
	"stylelint_lsp",
	"svelte",
	"tailwindcss",
	"taplo",
	"terraformls",
	"tflint",
	"vimls",
	"vue_ls",
	"yamlls",
}

require("mason-lspconfig").setup({
	ensure_installed = enabled_lsp_clients,
	-- NOTE: prevents mason-lspconfig from automatically enabling some LSP clients
	-- that are installed by mason-tool-installer (like buf)
	automatic_enable = false,
})

vim.lsp.config("*", utils.base_config)

-- NOTE: avoid using clangd for proto files
vim.lsp.config("clangd", {
	filetypes = { "c", "cpp" },
})

vim.lsp.enable(enabled_lsp_clients)

---@param top_level_table table<string, unknown>
---@return string[]
local function get_all_values_deep(top_level_table)
	---@type table<string, boolean>
	local values = {}

	---@param tbl table<string, unknown>
	local function walk_table(tbl)
		for _, value_or_tbl in pairs(tbl) do
			if type(value_or_tbl) == "table" then
				walk_table(value_or_tbl)
			else
				values[value_or_tbl] = true
			end
		end
	end

	walk_table(top_level_table)

	return vim.tbl_keys(values)
end

local function get_linters_to_install()
	return get_all_values_deep(require("lsp.nvim-lint").linters_by_ft)
end

local function get_formatters_to_install()
	return get_all_values_deep(require("lsp.conform-nvim").formatters_by_ft)
end

require("mason-tool-installer").setup({
	ensure_installed = vim.tbl_filter(function(tool_name)
		return require("mason-registry").has_package(tool_name)
	end, vim.list_extend(get_formatters_to_install(), get_linters_to_install())),
})

vim.diagnostic.config({
	float = {
		scope = "line",
		source = true,
	},
	jump = {
		wrap = false,
	},
	signs = {
		text = {
			[vim.diagnostic.severity.ERROR] = "󰅚 ",
			[vim.diagnostic.severity.WARN] = "󰀪 ",
			[vim.diagnostic.severity.HINT] = "󰌶 ",
			[vim.diagnostic.severity.INFO] = " ",
		},
		numhl = {
			[vim.diagnostic.severity.ERROR] = "DiagnosticSignError",
			[vim.diagnostic.severity.WARN] = "DiagnosticSignWarn",
			[vim.diagnostic.severity.HINT] = "DiagnosticSignHint",
			[vim.diagnostic.severity.INFO] = "DiagnosticSignInfo",
		},
	},
})
vim.keymap.set("n", "<Leader>d", function()
	vim.diagnostic.open_float()
end, {
	desc = "Show diagnostics for current line",
})

utils.setup_document_highlight()

require("auto-nvimrc").execute_nvimrcs()
