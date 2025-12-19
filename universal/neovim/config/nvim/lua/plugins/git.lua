return {
	{
		"tpope/vim-fugitive",
		cmd = { "G", "GBrowse" },
		ft = "gitcommit",
		dependencies = {
			"tpope/vim-rhubarb",
			"shumphrey/fugitive-gitlab.vim",
			"farhanmustar/fugitive-delta.nvim",
		},
	},
	{ "junegunn/gv.vim", cmd = "GV", dependencies = { "tpope/vim-fugitive" } },
	{
		"akinsho/git-conflict.nvim",
		event = { "BufReadPre", "BufNewFile" },
		-- NOTE: use stable releases.
		-- This also fixes a bug which causes git-conflict.nvim only work when
		-- neovim is opened in the root of the repository.
		version = "*",
		opts = {
			highlights = {
				-- NOTE: the default `current` highlight color is too heavy
				current = "DiffChange",
			},
			default_mappings = {
				ours = "co",
				theirs = "ct",
				none = "c0",
				both = "cb",
				next = "]x",
				prev = "[x",
			},
		},
	},
	{
		"voldikss/vim-floaterm",
		cmd = "FloatermNew",
		keys = {
			{
				"<Leader>G",
				"<cmd>FloatermNew --width=0.95 --height=0.95 lazygit<CR>",
				desc = "lazygit in floating terminal",
			},
		},
	},
	{
		"lewis6991/gitsigns.nvim",
		dependencies = {
			"nvim-lua/plenary.nvim",
		},
		event = { "BufReadPre", "BufNewFile" },
		config = function()
			local gitsigns = require("gitsigns")
			gitsigns.setup({
				on_attach = function(bufnr)
					local function map(mode, l, r, desc)
						vim.keymap.set(mode, l, r, { buffer = bufnr, desc = desc })
					end

					if vim.fn.maparg("[c", "n") == "" then
						map("n", "[c", function()
							if vim.wo.diff then
								vim.cmd.normal({ "[c", bang = true })
							else
								gitsigns.nav_hunk("prev")
							end
						end, "Previous hunk")
						map("n", "]c", function()
							if vim.wo.diff then
								vim.cmd.normal({ "]c", bang = true })
							else
								gitsigns.nav_hunk("next")
							end
						end, "Next hunk")
					else
						vim.notify("Skipping gitsigns hunk navigation mapping: already mapped", vim.log.levels.DEBUG)
					end

					map({ "n", "v" }, "<Leader>hs", "<cmd>Gitsigns stage_hunk<CR>", "Stage hunk")
					map({ "n", "v" }, "<Leader>hr", "<cmd>Gitsigns reset_hunk<CR>", "Reset hunk")
					map("n", "<Leader>htb", gitsigns.toggle_current_line_blame, "Toggle current line blame")
					map("n", "<Leader>htd", function()
						gitsigns.toggle_numhl()
						gitsigns.toggle_linehl()
					end, "Toggle diff highlights")
					map("n", "<Leader>hb", function()
						gitsigns.blame_line({ full = true })
					end, "Blame current line")
					map("n", "<Leader>hR", gitsigns.reset_buffer, "Reset changes in buffer")
					map("n", "<Leader>hp", gitsigns.preview_hunk, "Preview hunk")
					map("n", "<Leader>hi", gitsigns.preview_hunk_inline, "Preview hunk inline")
					map("n", "<Leader>hd", gitsigns.diffthis, "Diff this hunk")
				end,
			})
		end,
	},
	{
		"sindrets/diffview.nvim",
		dependencies = { "nvim-lua/plenary.nvim" },
		cmd = { "DiffviewOpen", "DiffviewFileHistory" },
		config = true,
	},
	{
		"esmuellert/vscode-diff.nvim",
		dependencies = { "MunifTanjim/nui.nvim" },
		cmd = "CodeDiff",
	},
}
