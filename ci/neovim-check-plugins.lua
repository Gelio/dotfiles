-- Checks that every plugin in lazy-lock.json is installed at its locked commit.
-- `Lazy! restore` exits 0 even when a plugin failed to clone. Run it with
-- `nvim -l ci/neovim-check-plugins.lua`, with the XDG variables already set.

local lockfile_path = vim.fn.stdpath("config") .. "/lazy-lock.json"
local lockfile = vim.json.decode(table.concat(vim.fn.readfile(lockfile_path), "\n"))
local plugins_dir = vim.fn.stdpath("data") .. "/lazy/"

---@type string[]
local failures = {}

for name, entry in pairs(lockfile) do
	local head = vim.system({ "git", "-C", plugins_dir .. name, "rev-parse", "HEAD" }, { text = true }):wait()
	if head.code ~= 0 then
		failures[#failures + 1] = name .. " is not installed"
	elseif vim.trim(head.stdout) ~= entry.commit then
		failures[#failures + 1] = ("%s is at %s, but lazy-lock.json has %s"):format(
			name,
			vim.trim(head.stdout),
			entry.commit
		)
	end
end

if #failures > 0 then
	table.sort(failures)
	print(table.concat(failures, "\n"))
	os.exit(1)
end

print(("All %d plugins match lazy-lock.json"):format(vim.tbl_count(lockfile)))
