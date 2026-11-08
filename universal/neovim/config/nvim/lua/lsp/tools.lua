-- The tools the config asks for, kept apart from lsp/init.lua so that
-- ci/neovim-install-all.lua checks the same lists.
local M = {}

M.enabled_lsp_clients = {
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

--- Names as nvim-lint and conform know them, which aren't all Mason packages.
---@return string[]
function M.get_formatters_and_linters()
	return vim.list_extend(
		get_all_values_deep(require("lsp.conform-nvim").formatters_by_ft),
		get_all_values_deep(require("lsp.nvim-lint").linters_by_ft)
	)
end

return M
