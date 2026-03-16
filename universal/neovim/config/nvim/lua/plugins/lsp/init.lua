return {
	{
		"neovim/nvim-lspconfig",
		config = function()
			require("lsp")
		end,
		dependencies = {
			{
				"pmizio/typescript-tools.nvim",
				dependencies = { "nvim-lua/plenary.nvim" },
				config = function()
					require("lsp.tsserver").setup()
				end,
			},
			{
				"mfussenegger/nvim-lint",
				event = { "BufReadPost", "BufNewFile" },
				config = function()
					local nvim_lint = require("lint")
					nvim_lint.linters_by_ft = require("lsp.nvim-lint").linters_by_ft

					local function is_lsp_popup_window()
						return not vim.o.buflisted and vim.o.buftype == "nofile"
					end

					local function is_bigfile()
						-- Relies on snacks.nvim/bigfile to change the filetype
						-- See https://github.com/folke/snacks.nvim/blob/2e284e23d956767a50321de9c9bb0c005ea7c51f/lua/snacks/bigfile.lua#L40
						return vim.o.filetype == "bigfile"
					end

					vim.api.nvim_create_autocmd({ "BufWinEnter", "BufWritePost" }, {
						group = vim.api.nvim_create_augroup("NvimLint", { clear = true }),
						callback = function()
							if vim.b.nvim_lint_disable then
								-- NOTE: do not lint buffers with `b:nvim_lint_disable` set to true
								return
							end

							if is_lsp_popup_window() then
								-- NOTE: do not lint LSP popup windows (e.g. hover, signature help)
								return
							end

							if is_bigfile() then
								return
							end

							nvim_lint.try_lint()
						end,
					})
				end,
			},
			{
				"stevearc/conform.nvim",
				opts = {
					formatters_by_ft = require("lsp.conform-nvim").formatters_by_ft,
					format_on_save = {
						lsp_format = "fallback",
						timeout_ms = 500,
					},
				},
				event = { "BufWritePre" },
				keys = {
					{
						"<Leader>F",
						function()
							require("conform").format({
								async = true,
								lsp_fallback = true,
							})
						end,
						mode = { "n", "v" },
						desc = "Format",
					},
				},
			},
			"b0o/SchemaStore.nvim",
			{
				"mason-org/mason.nvim",
				config = true,
				build = ":MasonUpdate",
			},
			"mason-org/mason-lspconfig.nvim",
			"WhoIsSethDaniel/mason-tool-installer.nvim",
			{
				"Gelio/auto-nvimrc",
				cmd = { "AutoNvimrcReset" },
				init = function()
					vim.api.nvim_create_user_command("AutoNvimrcReset", function()
						require("auto-nvimrc").reset()
					end, {})
				end,
			},
		},
	},

	{
		"oskarrrrrrr/symbols.nvim",
		version = "*",
		cmd = { "Symbols", "SymbolsToggle", "SymbolsOpen", "SymbolsClose" },
		keys = {
			{ "<Leader>so", "<cmd>Symbols<CR>", "Open symbols" },
		},
		config = function()
			local recipes = require("symbols.recipes")
			require("symbols").setup(recipes.DefaultFilters, recipes.AsciiSymbols, {})
		end,
	},
}
