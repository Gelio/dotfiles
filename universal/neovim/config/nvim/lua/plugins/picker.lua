return {
	{
		"ibhagwan/fzf-lua",
		dependencies = { "nvim-tree/nvim-web-devicons" },
		opts = {
			keymap = {
				fzf = {
					-- NOTE: inherit the default keymaps
					true,
					-- NOTE: ctrl-b (the default keymap for half-page-down) is
					-- inconvenient to use because it's also the tmux prefix.
					-- Thus, let's use ctrl-B (ctrl-shift-b) for half-page-up.
					["ctrl-B"] = "half-page-up",
					-- NOTE: use ctrl=F to match ctrl-B
					["ctrl-F"] = "half-page-down",

					-- NOTE: open all in quickfix list
					-- https://github.com/ibhagwan/fzf-lua/blob/743647f639a83e41e283d2d7daa03a85e1fbf951/lua/fzf-lua/profiles/telescope.lua#L81C7-L81C40
					["ctrl-q"] = "select-all+accept",
				},
			},
		},
		cmd = { "FzfLua" },
		keys = {
			{ "<Leader>ff", "<cmd>FzfLua files<CR>", desc = "Files (FzfLua)" },
			{ "<Leader>fb", "<cmd>FzfLua buffers<CR>", desc = "Buffers (FzfLua)" },
			{ "<Leader>fo", "<cmd>FzfLua oldfiles<CR>", desc = "Old files (FzfLua)" },
			{ "<Leader>fh", "<cmd>FzfLua helptags<CR>", desc = "Help tags (FzfLua)" },

			{ "<Leader>fg", "<cmd>FzfLua live_grep_native<CR>", desc = "Live grep (FzfLua)" },

			{ "<Leader>fGs", "<cmd>FzfLua git_status<CR>", desc = "Git status (FzfLua)" },
			{ "<Leader>fGf", "<cmd>FzfLua git_files<CR>", desc = "Git files (FzfLua)" },
			{ "<Leader>fGb", "<cmd>FzfLua git_branches<CR>", desc = "Git files (FzfLua)" },

			{ "<Leader>fr", "<cmd>FzfLua lsp_references<CR>", desc = "LSP references (FzfLua)" },
			{ "<Leader>fsd", "<cmd>FzfLua lsp_document_symbols<CR>", desc = "LSP document symbols (FzfLua)" },
			{ "<Leader>fsw", "<cmd>FzfLua lsp_workspace_symbols<CR>", desc = "LSP workspace symbols (FzfLua)" },
		},
		init = function()
			require("which-key").add({
				{ "<Leader>f", group = "Find (FzfLua)" },
			})
		end,
	},
}
