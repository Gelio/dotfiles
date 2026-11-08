-- Checks that every enabled plugin is installed at the commit in lazy-lock.json.
-- `Lazy! restore` exits 0 even when a plugin failed to clone. Starts from
-- lazy.nvim's list because the lockfile also has plugins with `enabled = false`,
-- which are never installed.
--
-- Run it with the XDG variables set, and with a fallback for when it errors:
-- nvim --headless -c 'luafile ci/neovim-check-plugins.lua' -c 'cquit 2'

local lockfile_path = vim.fn.stdpath("config") .. "/lazy-lock.json"
local lockfile = vim.json.decode(table.concat(vim.fn.readfile(lockfile_path), "\n"))

---@type string[]
local failures = {}
local checked = 0

for _, plugin in ipairs(require("lazy").plugins()) do
	checked = checked + 1
	local locked = lockfile[plugin.name]
	local head = vim.system({ "git", "-C", plugin.dir, "rev-parse", "HEAD" }, { text = true }):wait()

	if not locked then
		failures[#failures + 1] = plugin.name .. " is not in lazy-lock.json"
	elseif head.code ~= 0 then
		failures[#failures + 1] = plugin.name .. " is not installed"
	elseif vim.trim(head.stdout) ~= locked.commit then
		failures[#failures + 1] = ("%s is at %s, but lazy-lock.json has %s"):format(
			plugin.name,
			vim.trim(head.stdout),
			locked.commit
		)
	end
end

if #failures > 0 then
	table.sort(failures)
	print(table.concat(failures, "\n"))
	vim.cmd.cquit(1)
end

print(("All %d enabled plugins match lazy-lock.json"):format(checked))
vim.cmd.qall({ bang = true })
