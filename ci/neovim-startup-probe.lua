-- Runs inside the Neovim that ci/neovim-startup-check.lua starts, before
-- init.lua. Records every vim.notify call, force-loads the lazy-loaded plugins,
-- and writes what it saw to $NVIM_STARTUP_CHECK_RESULT. Judging that is the
-- job of the check script.

local result_path = assert(vim.env.NVIM_STARTUP_CHECK_RESULT, "NVIM_STARTUP_CHECK_RESULT is not set")

-- How long to let scheduled callbacks run after each step
local settle_ms = 1000

-- Everything else is force-loaded, because a bare start only runs the config
-- of plugins that aren't lazy-loaded, and those are most of the config.
---@type table<string, string> Plugin name to the reason it can't be loaded here
local never_force_load = {
	["nvim-dap-ui"] = "Needs nvim-nio, which the config doesn't install, so :DapUI is broken until that's added",
}

---@type { message: string, level: integer }[]
local notifications = {}

---@param level integer|string|nil
---@return integer
local function normalize_level(level)
	if type(level) == "string" then
		return vim.log.levels[level:upper()] or vim.log.levels.INFO
	end
	return level or vim.log.levels.INFO
end

-- Plugins replace vim.notify with their own during startup, so a plain wrapper
-- would stop seeing messages. Keep the field out of the table and answer it
-- from the metatable, so that the wrapper stays in front of any replacement.
local function install_notify_wrapper()
	local current_notify = vim.notify

	local function notify_wrapper(message, level, opts)
		notifications[#notifications + 1] = {
			message = type(message) == "string" and message or vim.inspect(message),
			level = normalize_level(level),
		}
		return current_notify(message, level, opts)
	end

	rawset(vim, "notify", nil)
	local metatable = getmetatable(vim)
	local original_index = metatable.__index
	metatable.__index = function(tbl, key)
		if key == "notify" then
			return notify_wrapper
		end
		return original_index(tbl, key)
	end
	metatable.__newindex = function(tbl, key, value)
		if key == "notify" then
			current_notify = value
		else
			rawset(tbl, key, value)
		end
	end
end

local function settle()
	vim.wait(settle_ms, function()
		return false
	end, 50)
end

local function force_load_plugins()
	local names = {}
	for _, plugin in ipairs(require("lazy").plugins()) do
		if not plugin._.loaded and not never_force_load[plugin.name] then
			names[#names + 1] = plugin.name
		end
	end
	table.sort(names)
	print("Force-loading: " .. table.concat(names, ", "))
	require("lazy").load({ plugins = names })
end

---@param probe_error string?
local function write_result(probe_error)
	local result = {
		notifications = notifications,
		messages = vim.api.nvim_exec2("messages", { output = true }).output,
		probe_error = probe_error,
	}
	vim.fn.writefile({ vim.json.encode(result) }, result_path)
end

local function run()
	-- lazy.nvim waits for UIEnter to fire VeryLazy, which never happens without a UI
	vim.api.nvim_exec_autocmds("UIEnter", { modeline = false })
	settle()
	force_load_plugins()
	settle()
end

install_notify_wrapper()

vim.api.nvim_create_autocmd("VimEnter", {
	once = true,
	callback = function()
		vim.schedule(function()
			local ok, err = xpcall(run, debug.traceback)
			write_result(not ok and err or nil)
			vim.cmd("qall!")
		end)
	end,
})
