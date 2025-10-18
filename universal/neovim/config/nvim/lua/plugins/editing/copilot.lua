local mcphub = {
	"ravitemer/mcphub.nvim",
	dependencies = {
		"nvim-lua/plenary.nvim",
	},
	lazy = true,
	build = "npm install -g mcp-hub@latest",
	config = function()
		require("mcphub").setup()
	end,
}

return {
	{ "github/copilot.vim" },
	mcphub,

	{
		"CopilotC-Nvim/CopilotChat.nvim",
		dependencies = {
			{ "github/copilot.vim" },
			{ "nvim-lua/plenary.nvim", branch = "master" },

			-- NOTE: make MCPHub a dependency of CopilotChat.nvim
			-- so they load together
			mcphub[1],
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
		},
	},

	{
		"olimorris/codecompanion.nvim",
		dependencies = {
			"nvim-lua/plenary.nvim",
			mcphub[1],
		},
		opts = function()
			local adapter = {
				name = "copilot",
				-- NOTE: according to Reddit, gpt-5-mini performs better than gpt-4.1
				model = "gpt-5-mini",
			}

			return {
				strategies = {
					chat = {
						adapter = adapter,
					},
					inline = {
						adapter = adapter,
					},
					cmd = {
						adapter = adapter,
					},
				},
				extensions = {
					mcphub = {
						callback = "mcphub.extensions.codecompanion",
						opts = {
							make_tools = true,
							show_server_tools_in_chat = true,
							add_mcp_prefix_to_tool_names = true,
							show_result_in_chat = true,
							make_vars = true,
							make_slash_commands = true,
						},
					},
				},
			}
		end,
		cmd = { "CodeCompanion", "CodeCompanionChat", "CodeCompanionActions", "CodeCompanionCmd" },
	},
}
