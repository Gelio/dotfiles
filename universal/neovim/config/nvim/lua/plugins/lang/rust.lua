return {
	{
		"Saecki/crates.nvim",
		event = "BufRead Cargo.toml",
		branch = "main",
		opts = {
			lsp = {
				enabled = true,
				actions = true,
				completion = true,
				hover = true,
			},
		},
	},
}
