return {
	{
		"nvim-treesitter/nvim-treesitter",
		build = ":TSUpdate",
		branch = "main",
		config = function()
			require("nvim-treesitter").install({
				"bash",
				"bibtex",
				"c",
				"comment",
				"css",
				"diff",
				"dockerfile",
				"git_rebase",
				"gitattributes",
				"gitcommit",
				"gitignore",
				"go",
				"gomod",
				"gowork",
				"graphql",
				"hcl",
				"hjson",
				"http",
				"ini",
				"java",
				"javascript",
				"jsdoc",
				"json",
				"json5",
				"jsonc",
				"latex",
				"lua",
				"luadoc",
				"make",
				"markdown",
				"markdown_inline",
				"nix",
				"prisma",
				"proto",
				"python",
				"query",
				"regex",
				"rust",
				"scss",
				"ssh_config",
				"styled",
				"svelte",
				"terraform",
				"tmux",
				"toml",
				"tsx",
				"typescript",
				"vim",
				"vimdoc",
				"vue",
				"yaml",
				"zsh",
			})

			vim.api.nvim_create_autocmd("FileType", {
				group = vim.api.nvim_create_augroup("TreesitterEnable", { clear = true }),
				callback = function()
					if vim.o.filetype == "bigfile" then
						return
					end

					-- Start treesitter for the current buffer, and ignore errors
					-- if there is no parser available.
					if pcall(vim.treesitter.start) then
						vim.bo.indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
					end
				end,
			})
		end,
	},
	{ "nvim-treesitter/nvim-treesitter-context", opts = {
		max_lines = "20%",
	} },
	{
		"nvim-treesitter/nvim-treesitter-textobjects",
		branch = "main",
		config = true,
		keys = function()
			local select_keys = vim
				.iter({
					{ keymap = "f", textobject = "function", label = "function" },
					{ keymap = "c", textobject = "call", label = "function call" },
				})
				:map(function(textobject)
					return {
						{
							"a" .. textobject.keymap,
							function()
								require("nvim-treesitter-textobjects.select").select_textobject(
									"@" .. textobject.textobject .. ".outer",
									"textobjects"
								)
							end,
							mode = { "x", "o" },
							desc = "Select " .. textobject.label .. " (outer)",
						},
						{
							"i" .. textobject.keymap,
							function()
								require("nvim-treesitter-textobjects.select").select_textobject(
									"@" .. textobject.textobject .. ".inner",
									"textobjects"
								)
							end,
							mode = { "x", "o" },
							desc = "Select " .. textobject.label .. " (inner)",
						},
					}
				end)
				:flatten()
				:totable()

			local swap_keys = {
				{
					"[a",
					function()
						require("nvim-treesitter-textobjects.swap").swap_previous("@parameter.inner")
					end,
					desc = "Swap with previous parameter",
				},
				{
					"]a",
					function()
						require("nvim-treesitter-textobjects.swap").swap_next("@parameter.inner")
					end,
					desc = "Swap with next parameter",
				},
			}

			return vim.list_extend(select_keys, swap_keys)
		end,
	},
	{
		"mfussenegger/nvim-treehopper",
		keys = {
			{
				"<Leader>sn",
				":<C-U>lua require('tsht').nodes()<CR>",
				mode = { "x", "o" },
				desc = "Select treesitter node",
			},
		},
	},
	{
		"https://gitlab.com/HiPhish/rainbow-delimiters.nvim",
		-- NOTE: this plugin uses submodules only for development.
		-- Let's skip them to speed up the installation and update process.
		submodules = false,
		config = function()
			local rainbow_delimiters = require("rainbow-delimiters")

			vim.g.rainbow_delimiters = {
				strategy = {
					[""] = rainbow_delimiters.strategy["global"],
					vim = rainbow_delimiters.strategy["local"],
				},
				query = {
					[""] = "rainbow-delimiters",
					lua = "rainbow-blocks",
				},
			}
		end,
	},
}
