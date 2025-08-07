return {
	{ "github/copilot.vim" },
	{
		"CopilotC-Nvim/CopilotChat.nvim",
		dependencies = {
			{ "github/copilot.vim" },
			{ "nvim-lua/plenary.nvim", branch = "master" },
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
			"CopilotChatAgents",
			"CopilotChatModels",
		},
	},
}
