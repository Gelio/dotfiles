-- NOTE: if fugitive is not loaded, using :Git results in an error about ambiguous user command.
require("lazy").load({ plugins = { "vim-fugitive" } })

vim.keymap.set("n", "<Leader>L", function()
	-- NOTE: parse the commit hash from the current line like:
	-- 1 file  | 5 5 | 42ce3970 (HEAD -> main, origin/main, origin/HEAD) chore(nvim): update lazy-lock.json Grzegorz Rozdzialik, 19 hours ago
	-- 7 files | 280 224 | c821561dcd8 fixup! chore(MIG-7928): add SQL file upload utilities and store Grzegorz Rozdzialik, 15 hours ago
	local line = vim.api.nvim_get_current_line()
	local commit_hash = line:match("%s*%d+ files?%s*|[^|]+|%s(%x+)%s")
	if commit_hash then
		vim.cmd("tab Git show " .. commit_hash)
	else
		vim.notify("Could not parse commit hash from the current line.", vim.log.levels.WARN)
	end
end, {
	desc = "Show the commit details of the commit under the cursor in Git history.",
})
