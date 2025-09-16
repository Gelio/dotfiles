return {
	{ "github/copilot.vim" },
	{
		"CopilotC-Nvim/CopilotChat.nvim",
		dependencies = {
			{ "github/copilot.vim" },
			{ "nvim-lua/plenary.nvim", branch = "master" },

			-- NOTE: make MCPHub a dependency of CopilotChat.nvim
			-- so they load together
			{
				"ravitemer/mcphub.nvim",
				dependencies = {
					"nvim-lua/plenary.nvim",
				},
				build = "npm install -g mcp-hub@latest",
				config = function()
					require("mcphub").setup()
				end,
			},
		},
		build = "make tiktoken",
		opts = {
			mappings = {
				complete = {
					-- NOTE: use <C-Space> since blink-cmp is disabled anyway,
					-- and the default <Tab> collides with copilot.vim
					insert = "<C-Space>",
				},
			},
		},
		cmd = {
			"CopilotChat",
			"CopilotChatOpen",
			"CopilotChatToggle",
			"CopilotChatPrompts",
			"CopilotChatModels",
			"MCPHub",
		},
	},
}
