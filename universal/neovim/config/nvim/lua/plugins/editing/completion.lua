return {
	{
		"saghen/blink.cmp",
		version = "*",
		event = { "InsertEnter", "CmdlineEnter" },

		dependencies = {
			"rafamadriz/friendly-snippets",
			{
				"saghen/blink.compat",
				version = "*",
				lazy = true,
				opts = {},
			},
			"hrsh7th/cmp-nvim-lua",
			"hrsh7th/cmp-calc",
			{
				"Gelio/cmp-natdat",
				opts = {
					cmp_kind_text = "NatDat",
					highlight_group = "BlinkCmpKindText",
				},
			},
			"moyiz/blink-emoji.nvim",
			{
				"David-Kunz/cmp-npm",
				lazy = true,
				dependencies = { "nvim-lua/plenary.nvim" },
				config = true,
				event = "BufRead package.json",
			},
		},

		opts = {
			keymap = {
				preset = "default",
				["<C-u>"] = { "scroll_documentation_up", "fallback" },
				["<C-d>"] = { "scroll_documentation_down", "fallback" },
				["<C-h>"] = { "snippet_backward", "fallback" },
				["<C-l>"] = { "snippet_forward", "fallback" },
			},
			appearance = {
				nerd_font_variant = "mono",
			},
			sources = {
				default = { "lsp", "path", "snippets", "buffer", "natdat", "emoji", "nvim_lua", "calc", "npm" },
				providers = {
					natdat = {
						name = "natdat",
						module = "blink.compat.source",
					},
					buffer = {
						min_keyword_length = 4,
					},
					emoji = {
						module = "blink-emoji",
						name = "Emoji",
						score_offset = 15,
					},
					["nvim_lua"] = {
						name = "nvim_lua",
						module = "blink.compat.source",
					},
					calc = {
						name = "calc",
						module = "blink.compat.source",
					},
					npm = {
						name = "npm",
						module = "blink.compat.source",
					},
				},
			},

			cmdline = {
				completion = {
					menu = {
						auto_show = true,
					},
				},
			},

			snippets = {
				preset = "default",
			},

			completion = {
				accept = {
					auto_brackets = {
						enabled = false,
					},
				},
				menu = {
					draw = {
						columns = function(ctx)
							if ctx.mode == "cmdline" then
								return {
									{ "label" },
								}
							else
								return {
									{ "label", "label_description", gap = 1 },
									{ "kind_icon", "kind", gap = 1 },
									{ "source_name" },
								}
							end
						end,
						components = {
							kind_icon = {
								text = function(ctx)
									if ctx.source_name == "natdat" then
										return "📅" .. ctx.icon_gap
									end

									return ctx.kind_icon .. ctx.icon_gap
								end,
							},
						},
					},
				},
				documentation = {
					auto_show = true,
					window = { border = "single" },
				},
			},
			signature = {
				-- NOTE: use built-in <C-j> signature
				enabled = false,
				window = { border = "single" },
			},
		},
	},
}
