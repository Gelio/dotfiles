-- Proves that the Neovim config starts cleanly. Run it with
-- `nvim -l ci/neovim-startup-check.lua`, with the XDG variables already pointing
-- at the config and at folders that hold the restored plugins.
--
-- Fails on `E123:`-style errors, tracebacks, and vim.notify at WARN or above,
-- unless the text matches the allowlist. Exit codes don't help here: Neovim
-- exits 0 after most startup errors.

-- Lua patterns, matched against one message or one line of output. Every entry
-- needs a reason, and an entry should be removed once the message is gone.
---@type { pattern: string, reason: string }[]
local allowlist = {}

local failure_patterns = { "%f[%w]E%d+:", "stack traceback:" }
local timeout_ms = 120000

local script_dir = vim.fs.dirname(vim.fs.abspath(arg[0]))

---@type string[]
local failures = {}

---@param text string
---@return boolean
local function is_allowlisted(text)
	for _, entry in ipairs(allowlist) do
		assert(entry.reason and entry.reason ~= "", "Allowlist entry without a reason: " .. entry.pattern)
		if text:find(entry.pattern) then
			return true
		end
	end
	return false
end

---@param source string
---@param text string?
local function scan_output(source, text)
	for _, line in ipairs(vim.split(text or "", "\n")) do
		for _, pattern in ipairs(failure_patterns) do
			if line:find(pattern) and not is_allowlisted(line) then
				failures[#failures + 1] = source .. ": " .. line
				break
			end
		end
	end
end

---@param notifications { message: string, level: integer }[]
local function scan_notifications(notifications)
	for _, notification in ipairs(notifications) do
		if notification.level >= vim.log.levels.WARN and not is_allowlisted(notification.message) then
			failures[#failures + 1] = "vim.notify at level " .. notification.level .. ": " .. notification.message
		end
	end
end

local function start_neovim()
	local result_path = vim.fn.tempname()
	local run = vim
		.system(
			{ "nvim", "--headless", "--cmd", "luafile " .. script_dir .. "/neovim-startup-probe.lua" },
			{ text = true, timeout = timeout_ms, env = { NVIM_STARTUP_CHECK_RESULT = result_path } }
		)
		:wait()

	print(run.stdout)
	print(run.stderr)

	if run.code ~= 0 then
		failures[#failures + 1] = "Neovim exited with code " .. run.code
	end
	scan_output("output", run.stdout)
	scan_output("output", run.stderr)

	-- Missing means that Neovim quit or hung before the probe finished
	if vim.fn.filereadable(result_path) == 0 then
		failures[#failures + 1] = "The startup probe wrote no result"
		return
	end

	local result = vim.json.decode(table.concat(vim.fn.readfile(result_path), "\n"))
	if result.probe_error ~= vim.NIL and result.probe_error ~= nil then
		failures[#failures + 1] = "The startup probe failed: " .. result.probe_error
	end
	scan_output(":messages", result.messages)
	scan_notifications(result.notifications)
end

start_neovim()

if #failures > 0 then
	print(("Startup check failed with %d problem(s):"):format(#failures))
	print(table.concat(vim.fn.uniq(vim.fn.sort(failures)), "\n"))
	os.exit(1)
end

print("Startup check passed")
