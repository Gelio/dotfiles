return {
	{
		"iamcco/markdown-preview.nvim",
		build = "cd app && npx --yes yarn install",
		ft = "markdown",
		config = function()
			vim.g.mkdp_echo_preview_url = true
		end,
	},

	{
		"AckslD/nvim-FeMaco.lua",
		cmd = { "FeMaco" },
		opts = {
			ft_from_lang = function(lang)
				if lang == "dataviewjs" then
					return "javascript"
				end

				return lang
			end,

			create_tmp_filepath = function(filetype)
				local extension = ""
				if filetype == "javascript" then
					extension = ".js"
				elseif filetype == "lua" then
					extension = ".lua"
				end

				return os.tmpname() .. extension
			end,

			ensure_newline = function(_base_filetype)
				return true
			end,
		},
	},

	{
		"mzlogin/vim-markdown-toc",
		ft = "markdown",
	},

	{
		"Gelio/nvim-relative-date",
		config = true,
		ft = "markdown",
		cmd = { "RelativeDateAttach", "RelativeDateToggle" },
	},

	{
		"davidmh/mdx.nvim",
		dependencies = { "nvim-treesitter/nvim-treesitter" },
	},
}
