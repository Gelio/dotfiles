return {
	{
		"stevearc/oil.nvim",
		opts = function()
			-- selene: allow(global_usage)
			function _G.oil_winbar()
				local current_dir = require("oil").get_current_dir()
				local head = vim.fn.fnamemodify(current_dir, ":~:h:h")
				local tail = vim.fn.fnamemodify(current_dir, ":h:t")
				return head .. "/%#StatusLine#" .. tail .. "/"
			end

			-- NOTE: must be the same as https://github.com/refractalize/oil-git-status.nvim/blob/4b5cf53842c17a09420919e655a6a559da3112d7/lua/oil-git-status.lua#L2C1-L2C66
			local namespace = vim.api.nvim_create_namespace("oil-git-status")

			---@param hl_group string
			local function is_unmodified_hl_group(hl_group)
				return hl_group == "OilGitStatusIndexUnmodified" or hl_group == "OilGitStatusWorkingTreeUnmodified"
			end

			---@param extmark vim.api.keyset.get_extmark_item
			local function jump_to_extmark_line(extmark)
				vim.cmd("normal! " .. extmark[2] + 1 .. "G")
			end

			return {
				columns = {
					"icon",
					"size",
				},
				keymaps = {
					["<C-v>"] = "actions.select_vsplit",
					["<C-x>"] = "actions.select_split",
					["<C-s>"] = "actions.select_split",
					["[c"] = {
						callback = function()
							local current_line_number = vim.fn.line(".") - 1
							if current_line_number == 0 then
								return
							end

							local extmarks = vim.api.nvim_buf_get_extmarks(
								0,
								namespace,
								0,
								{ current_line_number - 1, -1 },
								{ details = true }
							)
							local first_modified_extmark = vim.iter(extmarks):rev():find(
								---@param extmark vim.api.keyset.get_extmark_item
								function(extmark)
									return not is_unmodified_hl_group(extmark[4].sign_hl_group)
								end
							)

							if first_modified_extmark ~= nil then
								jump_to_extmark_line(first_modified_extmark)
							end
						end,
						desc = "Previous changed entry",
					},
					["]c"] = {
						callback = function()
							local current_line_number = vim.fn.line(".") - 1
							local last_line_number = vim.fn.line("$") - 1
							if current_line_number == last_line_number then
								return
							end

							local extmarks = vim.api.nvim_buf_get_extmarks(
								0,
								namespace,
								{ current_line_number + 1, 0 },
								-1,
								{ details = true }
							)
							local first_modified_extmark = vim.iter(extmarks):find(
								---@param extmark vim.api.keyset.get_extmark_item
								function(extmark)
									return not is_unmodified_hl_group(extmark[4].sign_hl_group)
								end
							)

							if first_modified_extmark ~= nil then
								jump_to_extmark_line(first_modified_extmark)
							end
						end,
						desc = "Next changed entry",
					},
				},
				win_options = {
					winbar = "%{%v:lua.oil_winbar()%}",
					-- NOTE: needed for oil-git-status.nvim icons
					signcolumn = "yes:2",
				},
			}
		end,
		dependencies = { "nvim-tree/nvim-web-devicons" },
		keys = {
			{ "-", "<cmd>Oil<CR>", desc = "Open parent directory" },
		},
		-- Load the plugin eagerly so oil takes over netrw when `nvim .`
		lazy = false,
	},
	{
		"refractalize/oil-git-status.nvim",
		dependencies = {
			"stevearc/oil.nvim",
		},
		ft = "oil",
		config = true,
	},
	{
		"ywpkwon/yank-path.nvim",
		cmd = "YankPath",
		opts = {
			default_mapping = false,
		},
	},
}
