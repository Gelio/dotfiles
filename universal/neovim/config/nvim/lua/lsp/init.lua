local utils = require("lsp.utils")

local enabled_lsp_clients = {
	"ansiblels",
	"basedpyright",
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
	"oxfmt",
	"prismals",
	"protols",
	"ruff",
	"rust_analyzer",
	"stylelint_lsp",
	"svelte",
	"tailwindcss",
	"taplo",
	"terraformls",
	"tflint",
	"ts_query_ls",
	"vimls",
	"vtsls",
	"yamlls",
}

---@param servers string[]
---@return string[]
local function filter_only_available_servers(servers)
	local available_servers = require("mason-lspconfig").get_available_servers()

	return vim.tbl_filter(function(server)
		return vim.tbl_contains(available_servers, server)
	end, servers)
end

if not require("skip-installs") then
	require("mason-lspconfig").setup({
		ensure_installed = filter_only_available_servers(enabled_lsp_clients),
		-- NOTE: prevents mason-lspconfig from automatically enabling some LSP clients
		-- that are installed by mason-tool-installer (like buf)
		automatic_enable = false,
	})
end

vim.lsp.config("*", utils.base_config)

-- NOTE: avoid using clangd for proto files
vim.lsp.config("clangd", {
	filetypes = { "c", "cpp" },
})

vim.lsp.enable(enabled_lsp_clients)

require("lsp.typescript")

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
			elseif type(value_or_tbl) == "string" then
				-- Skips non-string options, such as stop_after_first
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

---@return string[]
local function get_mason_packages_to_install()
	-- NOTE: formatters and linters can be names that only conform or nvim-lint
	-- know, like trim_whitespace. Compare against the list of names because
	-- `has_package` logs "Cannot find package" for each of those.
	local mason_packages = require("mason-registry").get_all_package_names()

	return vim.tbl_filter(function(tool_name)
		return vim.tbl_contains(mason_packages, tool_name)
	end, vim.list_extend(get_formatters_to_install(), get_linters_to_install()))
end

if not require("skip-installs") then
	require("mason-tool-installer").setup({
		ensure_installed = get_mason_packages_to_install(),
	})
end

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

vim.api.nvim_create_autocmd("LspAttach", {
	group = vim.api.nvim_create_augroup("LspAttach_SetupKeymaps", { clear = true }),
	callback = function(event)
		utils.setup_lsp_keymaps(event.buf)
	end,
})

require("auto-nvimrc").execute_nvimrcs()
