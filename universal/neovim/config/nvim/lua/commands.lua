local M = {}

---@param language string
---@return string
local function get_spellfile(language)
	local nvim_config_path = vim.opt.runtimepath:get()[1]
	local encoding = vim.o.encoding
	local spellfile_name = language .. "." .. encoding .. ".add"

	return vim.fs.joinpath(nvim_config_path, "spell", spellfile_name)
end

---Sets the 'spellfile' based on the spelllangs
---@param spelllangs string[]? For example {"en", "pl"}. Defaults to 'spelllang'
function M.set_spellfile(spelllangs)
	spelllangs = spelllangs or vim.opt.spelllang:get()
	vim.opt.spellfile = vim.tbl_map(get_spellfile, spelllangs)
end

local function register_code_yank_user_command()
	vim.api.nvim_create_user_command("CodeYank", function(opts)
		local filepath = vim.fn.expand("%:p")
		local ft = vim.bo.filetype
		local lang = ft ~= "" and ft or ""

		local line_start = opts.line1
		local line_end = opts.line2

		local lines = vim.api.nvim_buf_get_lines(0, line_start - 1, line_end, false)
		local code_block = table.concat(lines, "\n")

		local header
		if line_start == line_end then
			header = string.format("%s:%d", filepath, line_start)
		else
			header = string.format("%s:%d-%d", filepath, line_start, line_end)
		end

		local content = string.format("%s\n```%s\n%s\n```", header, lang, code_block)

		vim.fn.setreg("+", content)

		vim.notify(string.format("Yanked %d line(s) context", #lines), vim.log.levels.INFO)
	end, {
		range = true,
		desc = "Yank file path, line numbers, and selected code to clipboard",
	})
end

function M.setup()
	vim.api.nvim_create_user_command("SpellFile", function(params)
		if #params.fargs == 1 then
			M.set_spellfile({ params.fargs[1] })
		else
			M.set_spellfile()
		end
	end, {
		desc = "Set the spellfile based on the language",
		complete = function()
			return { "pl", "en" }
		end,
		nargs = "?",
	})

	register_code_yank_user_command()
end

return M
