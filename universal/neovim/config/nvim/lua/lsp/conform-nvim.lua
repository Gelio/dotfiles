local formatters_by_ft = {
	lua = { "stylua" },
	sh = { "shfmt" },
	go = { "gofumpt" },
	plantuml = { "trim_whitespace" },
	python = { "ruff_organize_imports", "ruff_format" },
	proto = { "buf" },
	query = { "format-queries" },
}

local prettierd_filetypes = {
	"javascript",
	"javascriptreact",
	"typescript",
	"typescriptreact",
	"css",
	"scss",
	"less",
	"html",
	"markdown.mdx",
	"graphql",
	"handlebars",
}

for _, prettierd_filetype in ipairs(prettierd_filetypes) do
	local existing_ft_formatters = formatters_by_ft[prettierd_filetype]

	if existing_ft_formatters ~= nil then
		table.insert(existing_ft_formatters, "prettierd")
	else
		formatters_by_ft[prettierd_filetype] = { "prettierd" }
	end
end

-- oxfmt only runs where its config exists, so prettierd handles everything else
for _, oxfmt_filetype in ipairs({ "json", "jsonc", "yaml", "markdown" }) do
	formatters_by_ft[oxfmt_filetype] = { "oxfmt", "prettierd", stop_after_first = true }
end

---@param cwd string
---@param args string[]
---@return vim.SystemCompleted|nil result nil when mise can't be started
local function run_mise(cwd, args)
	local ok, result = pcall(function()
		return vim.system(vim.list_extend({ "mise" }, args), { cwd = cwd, text = true, timeout = 1000 }):wait()
	end)
	return ok and result or nil
end

--- `mise exec` trusts an untrusted config instead of refusing when it has no
--- terminal to ask on, and then runs the templates in it. `trust --show` covers
--- parent directories' configs too and doesn't evaluate any of them.
---@param cwd string
---@return boolean
local function mise_trusts_configs(cwd)
	local result = run_mise(cwd, { "trust", "--show" })
	if result == nil or result.code ~= 0 then
		return false
	end

	for line in vim.gsplit(result.stdout, "\n", { plain = true, trimempty = true }) do
		if not vim.endswith(line, ": trusted") then
			return false
		end
	end
	return true
end

return {
	formatters_by_ft = formatters_by_ft,
	formatters = {
		oxfmt = {
			-- `mise exec` so that the version is the one from the root mise.toml that
			-- CI uses, not Mason's. That release binary has no --stdin-filepath, hence
			-- the temporary file. Files in ignorePatterns count as unmatched.
			command = "mise",
			args = { "exec", "--", "oxfmt", "--no-error-on-unmatched-pattern", "$FILENAME" },
			stdin = false,
			env = { MISE_EXEC_AUTO_INSTALL = "0" },
			-- Not conform's default list, which also matches every Vite project
			cwd = function(_, ctx)
				return vim.fs.root(ctx.dirname, { ".oxfmtrc.json", ".oxfmtrc.jsonc" })
			end,
			require_cwd = true,
			condition = function(self, ctx)
				local cwd = self:cwd(ctx)
				if cwd == nil or not mise_trusts_configs(cwd) then
					return false
				end

				-- Only ask once the configs are trusted. Fails when oxfmt isn't pinned
				-- or isn't installed, and installs nothing.
				local result = run_mise(cwd, { "which", "oxfmt" })
				return result ~= nil and result.code == 0
			end,
		},
	},
}
