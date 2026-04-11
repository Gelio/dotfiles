return {
	-- NOTE: manually specify nested plugins/ directories to import
	-- Otherwise, only the init.lua module is imported from them.
	{ import = "plugins/editing" },
	{ import = "plugins/extra" },
	{ import = "plugins/lang" },
	{ import = "plugins/lsp" },

	{ "tpope/vim-sensible" },

	{
		"tweekmonster/startuptime.vim",
		cmd = "StartupTime",
	},

	{ "kevinhwang91/nvim-bqf", ft = "qf" },
	{ "stevearc/quicker.nvim", ft = "qf", opts = {
		opts = {
			number = true,
			relativenumber = true,
		},
	} },

	{
		"nvim-lua/plenary.nvim",
		config = function()
			vim.api.nvim_create_autocmd("BufEnter", {
				pattern = { "*/tests/*_spec.lua", "*/test/*_spec.lua" },
				group = vim.api.nvim_create_augroup("PlenaryTests", { clear = true }),
				callback = function()
					vim.keymap.set("n", "<Leader>te", "<Plug>PlenaryTestFile", { buffer = 0, remap = true })
				end,
			})
		end,
	},

	{
		"sindrets/winshift.nvim",
		cmd = "WinShift",
		keys = {
			{ "<C-W>m", "<cmd>WinShift<CR>", "Window shift mode" },
			{ "<C-W><C-M>", "<cmd>WinShift<CR>", "Window shift mode" },
		},
		config = true,
	},
}
