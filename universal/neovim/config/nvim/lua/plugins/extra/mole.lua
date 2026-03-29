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
				local desc = vim.fn.input("Session description (default: " .. basename .. "): ")
				if desc == "" then
					desc = basename
				end
				return "session_" .. os.date("%Y-%m-%d_%H-%M-%S") .. "-" .. desc
			end,
		},
	},
}
