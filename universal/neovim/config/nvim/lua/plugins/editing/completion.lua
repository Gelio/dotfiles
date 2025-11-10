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

		opts = function()
			-- Workaround for line-wrapping when moving between completion items
			-- https://github.com/saghen/blink.cmp/issues/1445
			local function apply_auto_wrap_workaround()
				vim.api.nvim_create_autocmd("User", {
					pattern = "BlinkCmpMenuOpen",
					callback = function()
						local formatoptions = vim.opt.formatoptions:get()
						if formatoptions.t then
							vim.b.restore_formatoptions_t = true
							vim.opt.formatoptions:remove("t")
						end
					end,
				})

				vim.api.nvim_create_autocmd("User", {
					pattern = "BlinkCmpMenuClose",
					callback = function()
						if vim.b.restore_formatoptions_t then
							vim.opt.formatoptions:append("t")
							vim.b.restore_formatoptions_t = nil
						end
					end,
				})
			end

			apply_auto_wrap_workaround()

			return {
				enabled = function()
					-- NOTE: copilot-chat has its own completion
					return vim.bo.filetype ~= "copilot-chat"
				end,
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
					per_filetype = {
						sql = { "dadbod", "snippets", "buffer" },
						plsql = { "dadbod", "snippets", "buffer" },
					},
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
						dadbod = {
							name = "Dadbod",
							module = "vim_dadbod_completion.blink",
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
						border = "none",
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
					},
				},
				signature = {
					-- NOTE: use built-in <C-j> signature
					enabled = false,
				},
			}
		end,
	},
}
