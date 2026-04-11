local mcphub = {
	"ravitemer/mcphub.nvim",
	dependencies = {
		"nvim-lua/plenary.nvim",
	},
	cmd = "MCPHub",
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
		"olimorris/codecompanion.nvim",
		dependencies = {
			"nvim-lua/plenary.nvim",
			mcphub[1],
			"ravitemer/codecompanion-history.nvim",
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
				display = {
					diff = {
						provider_opts = {
							inline = {
								layout = "buffer",
							},
						},
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
					history = {
						enabled = true,
					},
				},
			}
		end,
		cmd = { "CodeCompanion", "CodeCompanionChat", "CodeCompanionActions", "CodeCompanionCmd", "CodeCompanionHistory" },
	},
}
