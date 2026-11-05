return {
	{
		"nvzone/typr",
		dependencies = "nvzone/volt",
		opts = {
			on_attach = function(buf)
				-- Disable blink.cmp
				vim.b[buf].completion = false
			end,
		},
		cmd = { "Typr", "TyprStats" },
	},
}
