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
		"lewis6991/gitsigns.nvim",
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
		"esmuellert/codediff.nvim",
		dependencies = { "MunifTanjim/nui.nvim" },
		cmd = { "CodeDiff", "CodeDiffCommit" },
		config = function()
			require("codediff").setup({
				diff = {
					compute_moves = true,
				},
			})

			vim.api.nvim_create_user_command("CodeDiffToggleWhitespace", function()
				local config = require("codediff.config")
				local auto_refresh = require("codediff.ui.auto_refresh")
				local lifecycle = require("codediff.ui.lifecycle")

				config.options.diff.ignore_trim_whitespace = not config.options.diff.ignore_trim_whitespace

				local tabpage = vim.api.nvim_get_current_tabpage()
				local session = lifecycle.get_session(tabpage)
				if session then
					auto_refresh.trigger(session.modified_bufnr)
				end

				vim.notify(
					"Ignore trim whitespace: " .. tostring(config.options.diff.ignore_trim_whitespace),
					vim.log.levels.INFO
				)
			end, { desc = "Toggle codediff ignore_trim_whitespace" })

			vim.api.nvim_create_user_command("CodeDiffCommit", function(opts)
				local ref = opts.args

				vim.cmd.CodeDiff({ args = { string.format("%s~...%s", ref, ref) } })
			end, { desc = "Show diff of the specified commit (like git show)", nargs = 1 })
		end,
	},
}
