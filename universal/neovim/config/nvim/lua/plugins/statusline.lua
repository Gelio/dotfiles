return {
	{
		"nvim-lualine/lualine.nvim",
		dependencies = { "nvim-tree/nvim-web-devicons" },
		event = "VeryLazy",
		opts = function()
			---Use global status line instead of per-window status lines
			local global_status = false

			local dap_extension = {
				sections = {
					lualine_a = { "mode", "filename" },
				},
				inactive_sections = {
					lualine_a = { "filename" },
				},
				filetypes = {
					"dapui_scopes",
					"dapui_watches",
					"dapui_stacks",
					"dapui_breakpoints",
					"dap-repl",
				},
			}
			--- Source: https://github.com/nvim-lualine/lualine.nvim/wiki/Component-snippets#truncating-components-in-smaller-window
			--- @param trunc_width? number trunctates component when screen width is less than trunc_width
			--- @param trunc_len? number truncates component to trunc_len number of chars
			--- @param hide_width? number hides component when window width is smaller then hide_width
			--- @param no_ellipsis? boolean whether to disable adding '...' at end after truncation
			--- return function that can format the component accordingly
			local function trunc(trunc_width, trunc_len, hide_width, no_ellipsis)
				return function(str)
					local win_width = global_status and vim.go.columns or vim.fn.winwidth(0)
					if hide_width and win_width < hide_width then
						return ""
					elseif trunc_width and trunc_len and win_width < trunc_width and #str > trunc_len then
						return str:sub(1, trunc_len) .. (no_ellipsis and "" or "...")
					end
					return str
				end
			end
			local filename_section = {
				"filename",
				path = 1, -- NOTE: show relative file path
			}

			return {
				options = {
					globalstatus = global_status,
				},
				sections = {
					lualine_a = { "mode" },
					lualine_b = {
						{ "branch", fmt = trunc(150, 20, 120) },
						{
							"diff",
							source = function()
								local gitsigns_stats = vim.b.gitsigns_status_dict
								if not gitsigns_stats then
									return {}
								end
								return {
									added = gitsigns_stats.added,
									modified = gitsigns_stats.changed,
									removed = gitsigns_stats.removed,
								}
							end,
						},
					},
					lualine_c = {
						{
							function()
								return require("arrow.statusline").text_for_statusline_with_icons()
							end,
							cond = function()
								local success = pcall(function()
									return require("arrow.statusline")
								end)
								return success
							end,
						},
						filename_section,
					},
					lualine_x = {
						{
							"diagnostics",
							sources = { "nvim_diagnostic" },
						},
						{ "encoding", fmt = trunc(nil, nil, 150) },
						{ "fileformat", fmt = trunc(nil, nil, 150) },
						{ "filetype", fmt = trunc(150, 8) },
					},
					lualine_y = { { "progress", fmt = trunc(nil, nil, 120) } },
					lualine_z = { "location" },
				},
				inactive_sections = {
					lualine_a = {},
					lualine_b = {},
					lualine_c = { filename_section },
					lualine_x = { "location" },
					lualine_y = {},
					lualine_z = {},
				},
				extensions = {
					"fugitive",
					"lazy",
					"man",
					"mason",
					"oil",
					"quickfix",
					"trouble",
					-- TODO: consider using the "nvim-dap-ui" extension
					dap_extension,
				},
			}
		end,
	},

	{
		"akinsho/bufferline.nvim",
		dependencies = "nvim-tree/nvim-web-devicons",
		event = "VeryLazy",
		opts = function()
			local filetype_to_tab_name = {
				TelescopePrompt = "Telescope",
				quickfix = "quickfix",
				fugitive = "Fugitive",
				trouble = "Trouble",
			}

			return {
				options = {
					mode = "tabs",
					numbers = "ordinal", -- matches the tab numbers
					always_show_bufferline = false,
					name_formatter = function(tab)
						local winid = vim.api.nvim_tabpage_get_win(tab.tabnr)
						local bufnr = vim.api.nvim_win_get_buf(winid)
						local filetype = vim.bo[bufnr].filetype

						---@type string | nil
						local tab_name = filetype_to_tab_name[filetype]
						if tab_name ~= nil then
							return tab_name
						end

						-- NOTE: default name if it's not a special buffer
						return nil
					end,
				},
			}
		end,
	},
}
