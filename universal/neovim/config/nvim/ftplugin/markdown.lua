if vim.fn.getenv("CLAUDE_CODE_ENTRYPOINT") == "cli" then
	-- Claude Code uses /tmp for temporary files when editing them in the default editor.
	-- This messes up path autocompletion.
	-- Thus, let's add the current directory to the path, so that autocompletion works as expected.
	vim.opt.path:append(",,")

	vim.print("Calling blink.cmp setup")
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
							vim.print("get_cwd called with bufnr:", context.bufnr)
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
