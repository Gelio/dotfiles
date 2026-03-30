return {
	{
		"zion-off/mole.nvim",
		dependencies = {
			"MunifTanjim/nui.nvim",
		},
		cmd = { "MoleStart", "MoleResume", "MoleToggle" },
		opts = {
			session_name = function()
				local basename = vim.fn.fnamemodify(vim.fn.getcwd(), ":t")
				local default_session_name = "session_" .. os.date("%Y-%m-%d_%H-%M-%S") .. "-" .. basename
				return vim.fn.input("Session name: ", default_session_name)
			end,
		},
	},
}
