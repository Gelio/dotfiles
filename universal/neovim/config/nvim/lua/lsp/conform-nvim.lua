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
			require_cwd = true,
		},
	},
}
