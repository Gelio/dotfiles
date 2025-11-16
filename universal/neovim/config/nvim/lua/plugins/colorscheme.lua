local colorscheme_priority = 1000

return {
	{
		"sainnhe/gruvbox-material",
		enabled = false,
		priority = colorscheme_priority,
		config = function()
			vim.g.gruvbox_material_better_performance = 1
			vim.g.gruvbox_material_diagnostic_virtual_text = "colored"
			vim.g.gruvbox_material_diagnostic_text_highlight = 1
			vim.g.gruvbox_material_diagnostic_line_highlight = 1
			vim.g.gruvbox_material_ui_contrast = "high"
			vim.cmd.colorscheme("gruvbox-material")
		end,
	},

	{
		"catppuccin/nvim",
		name = "catppuccin",
		enabled = true,
		priority = colorscheme_priority,
		config = function()
			local color_utils = require("catppuccin.utils.colors")

			require("catppuccin").setup({
				highlight_overrides = {
					all = function(colors)
						return {
							LineNr = { fg = color_utils.brighten(colors.overlay0, 0.1) },
						}
					end,
				},
				integrations = {
					diffview = true,
					fidget = true,
					fzf = true,
					headlines = true,
					treesitter_context = true,
					ufo = true,
					lightspeed = true,
					rainbow_delimiters = true,
					render_markdown = true,
					dadbod_ui = true,
					mason = true,
					copilot_vim = true,
					nvim_surround = true,
					lsp_trouble = true,
					which_key = true,
				},
			})

			vim.cmd.colorscheme("catppuccin")
		end,
	},
	{
		"navarasu/onedark.nvim",
		priority = colorscheme_priority,
		enabled = false,
		config = function()
			require("onedark").setup({
				style = "warm",
				highlights = {
					-- NOTE: a raw hex color to be brighter than `$grey` but darker than `$light_grey`.
					--`$light_grey` is too close to `$fg`, so I cannot use it.
					LineNr = { fg = "#7D7E81" },
				},
			})

			vim.cmd.colorscheme("onedark")
		end,
	},
}
