--- Codex writes the prompt to `$CODEX_HOME/editor/*.md` when editing it in the external editor.
local function is_codex_prompt()
	local codex_home = vim.env.CODEX_HOME or vim.fs.joinpath(vim.env.HOME, ".codex")
	local editor_dir = vim.fs.normalize(vim.fs.joinpath(codex_home, "editor"))
	local bufname = vim.fs.normalize(vim.api.nvim_buf_get_name(0))
	return vim.fs.dirname(bufname) == editor_dir
end

if vim.fn.getenv("CLAUDE_CODE_ENTRYPOINT") == "cli" or is_codex_prompt() then
	-- Wrap long lines at word boundaries to make writing prompts easier.
	vim.opt_local.wrap = true
	vim.opt_local.linebreak = true

	-- Claude Code and Codex use temporary files outside the project when editing them in the default editor.
	-- This messes up path autocompletion.
	-- Thus, let's add the current directory to the path, so that autocompletion works as expected.
	vim.opt.path:append(",,")

	require("blink.cmp.config").merge_with({
		sources = {
			providers = {
				path = {
					opts = {
						get_cwd = function(context)
							-- The first buffer is always the Markdown prompt file.
							-- For that buffer, let's also reconfigure blink.cmp to use the
							-- current directory as the path, so that autocompletion works as
							-- expected.
							if context.bufnr == 1 then
								return vim.fn.getcwd()
							end
							return vim.fn.expand(("#%d:p:h"):format(context.bufnr))
						end,
					},
				},
			},
		},
	})
end
