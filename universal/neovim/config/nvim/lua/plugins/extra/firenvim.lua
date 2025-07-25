local function create_markdownlint_config()
	local markdownlintrc_path = vim.fs.joinpath(vim.fn.getcwd(), ".markdownlintrc")

	local async = require("plenary.async")
	local err, fd = async.uv.fs_open(
		markdownlintrc_path,
		"w",
		-- 0o666
		438
	)
	assert(not err, err)

	require("plenary.async.util").scheduler()
	local markdownlintrc_content = vim.fn.trim([[
{
	"line-length": false,
	"first-line-heading": false
}
]])

	err, _ = async.uv.fs_write(fd, markdownlintrc_content)
	assert(not err, err)

	err = async.uv.fs_close(fd)
	assert(not err, err)
end

return {
	{
		"glacambre/firenvim",
		build = ":call firenvim#install(0)",
		config = function()
			if not vim.g.started_by_firenvim then
				return
			end

			local default_settings = {
				takeover = "never",
				priority = 0,
				cmdline = "neovim",
			}
			vim.g.firenvim_config = {
				localSettings = {
					["https://(github.com|gitlab.com|mattermost\\.).*"] = vim.tbl_extend("error", default_settings, {
						filename = "{hostname%32}_{pathname%32}_{selector%32}_{timestamp%32}.md",
					}),
					[".*"] = default_settings,
				},
			}

			-- https://github.com/glacambre/firenvim#building-a-firenvim-specific-config
			local group_id = vim.api.nvim_create_augroup("FirenvimConfig", { clear = true })

			vim.api.nvim_create_autocmd("BufEnter", {
				pattern = "mail.google.com_*.txt",
				group = group_id,
				callback = function()
					vim.bo.filetype = "markdown"
					vim.o.textwidth = 80
				end,
			})

			-- WORKAROUND: on HiDPI screens, the font size is too large by default
			vim.o.guifont = ":h20"

			vim.api.nvim_create_autocmd("UIEnter", {
				group = group_id,
				callback = function()
					vim.o.cmdheight = 1

					local min_lines = 18
					if vim.o.lines < min_lines then
						vim.o.lines = min_lines
					end

					vim.o.wrap = true
					vim.o.linebreak = true

					require("plenary.async").void(create_markdownlint_config)()
				end,
			})
		end,
	},
}
