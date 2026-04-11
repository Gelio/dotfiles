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
