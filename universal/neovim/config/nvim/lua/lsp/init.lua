local utils = require("lsp.utils")

local tools = require("lsp.tools")

local enabled_lsp_clients = tools.enabled_lsp_clients

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

---@return string[]
local function get_mason_packages_to_install()
	-- NOTE: formatters and linters can be names that only conform or nvim-lint
	-- know, like trim_whitespace. Compare against the list of names because
	-- `has_package` logs "Cannot find package" for each of those.
	local mason_packages = require("mason-registry").get_all_package_names()

	return vim.tbl_filter(function(tool_name)
		return vim.tbl_contains(mason_packages, tool_name)
	end, tools.get_formatters_and_linters())
end

local skip_installs = require("skip-installs")
-- NOTE: setup still has to run when skipping. The plugin checks for updates on
-- VimEnter, which contacts the Mason registry unless run_on_start is off.
require("mason-tool-installer").setup({
	ensure_installed = skip_installs and {} or get_mason_packages_to_install(),
	run_on_start = not skip_installs,
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

vim.api.nvim_create_autocmd("LspAttach", {
	group = vim.api.nvim_create_augroup("LspAttach_SetupKeymaps", { clear = true }),
	callback = function(event)
		utils.setup_lsp_keymaps(event.buf)
	end,
})

require("auto-nvimrc").execute_nvimrcs()
