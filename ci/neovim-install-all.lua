-- Runs the plugin builds and installs every Mason package and Treesitter parser
-- that the config asks for, and fails unless all of them really are there.
-- Exit codes and the startup check don't prove this: plugin builds, Mason and
-- Treesitter all report failures only through logs and carry on.
--
-- Run it through the startup check, with the XDG variables set and after the
-- plugins are installed, so that errors and warnings from installing fail too:
-- nvim -l ci/neovim-startup-check.lua ci/neovim-install-all.lua

-- Requested formatter and linter names that aren't Mason packages, so that
-- lsp/init.lua is right to drop them. Anything else that Mason doesn't know is
-- a typo and fails the job.
---@type table<string, string> Name to the reason it isn't a Mason package
local expected_dropped = {
	buf_lint = "nvim-lint's name for `buf lint`, provided by the buf package",
	["format-queries"] = "conform's name for a script that ships with nvim-treesitter",
	ruff_format = "conform's name for `ruff format`, provided by the ruff package",
	ruff_organize_imports = "conform's name for `ruff check --select I`, provided by the ruff package",
	trim_whitespace = "conform's built-in formatter, which only needs awk",
}

local registry_timeout_ms = 5 * 60 * 1000
local mason_timeout_ms = 40 * 60 * 1000
local treesitter_timeout_ms = 30 * 60 * 1000
local poll_ms = 200

---@param problems string[]
---@param heading string
local function fail_if_any(problems, heading)
	if #problems == 0 then
		return
	end
	table.sort(problems)
	error(heading .. "\n" .. table.concat(problems, "\n"))
end

local function check_plugin_builds()
	local plugin_names = {}
	for _, plugin in ipairs(require("lazy").plugins()) do
		if plugin.build then
			plugin_names[#plugin_names + 1] = plugin.name
		end
	end
	assert(#plugin_names > 0, "No plugin has a build step")

	-- Rerun here, because the results of the builds that ran when the plugins
	-- were cloned are only in the memory of the process that cloned them.
	require("lazy.manage").build({ wait = true, show = false, plugins = plugin_names })

	local problems = {}
	for _, plugin in ipairs(require("lazy").plugins()) do
		for _, task in ipairs(plugin._.tasks or {}) do
			if task:has_errors() then
				problems[#problems + 1] = ("%s: %s"):format(plugin.name, task:output(vim.log.levels.ERROR))
			end
		end
	end
	fail_if_any(problems, "Plugin builds failed:")
	print(("Plugin builds succeeded: %s"):format(table.concat(plugin_names, ", ")))
end

local function refresh_mason_registry()
	local registry = require("mason-registry")
	local done, success, err = false, false, nil
	registry.update(function(update_success, update_err)
		done, success, err = true, update_success, update_err
	end)
	assert(
		vim.wait(registry_timeout_ms, function()
			return done
		end, poll_ms),
		"Timed out refreshing the Mason registry"
	)
	assert(success, "Refreshing the Mason registry failed: " .. vim.inspect(err))
	assert(#registry.get_all_package_names() > 0, "The Mason registry has no packages")
end

--- Compares every requested name with the registry, instead of trusting the
--- filters in lsp/init.lua, which drop unknown names silently.
---@return string[] packages Mason package names, sorted and unique
local function get_requested_mason_packages()
	local tools = require("lsp.tools")
	local registry_names = {}
	for _, name in ipairs(require("mason-registry").get_all_package_names()) do
		registry_names[name] = true
	end
	local lspconfig_to_package = require("mason-lspconfig").get_mappings().lspconfig_to_package

	local packages, problems, dropped = {}, {}, {}

	for _, client in ipairs(tools.enabled_lsp_clients) do
		local package_name = lspconfig_to_package[client]
		if package_name and registry_names[package_name] then
			packages[package_name] = true
		else
			problems[#problems + 1] = "LSP client without a Mason package: " .. client
		end
	end

	for _, name in ipairs(tools.get_formatters_and_linters()) do
		if expected_dropped[name] then
			dropped[name] = true
			if registry_names[name] then
				problems[#problems + 1] = "Expected to be dropped, but Mason has it: " .. name
			end
		elseif registry_names[name] then
			packages[name] = true
		else
			problems[#problems + 1] = "Formatter or linter unknown to Mason: " .. name
		end
	end

	for name in pairs(expected_dropped) do
		if not dropped[name] then
			problems[#problems + 1] = "Expected to be dropped, but nothing requests it: " .. name
		end
	end

	fail_if_any(problems, "The requested tools don't match the Mason registry:")

	local sorted = vim.tbl_keys(packages)
	table.sort(sorted)
	assert(#sorted > 0, "No Mason packages were requested")
	return sorted
end

---@param package_names string[]
local function install_mason_packages(package_names)
	local registry = require("mason-registry")
	local packages = vim.tbl_map(registry.get_package, package_names)

	-- mason-lspconfig already started the language servers from the config, so
	-- only start what isn't running. The result is read from disk afterwards.
	for _, package in ipairs(packages) do
		if not package:is_installed() and not package:is_installing() then
			package:install()
		end
	end

	local finished = vim.wait(mason_timeout_ms, function()
		return vim.iter(packages):all(function(package)
			return not package:is_installing()
		end)
	end, poll_ms)
	assert(finished, "Timed out installing Mason packages")

	local problems = {}
	for _, package in ipairs(packages) do
		if not package:is_installed() then
			problems[#problems + 1] = package.name
		end
	end
	fail_if_any(problems, "Mason packages that failed to install, see mason.log:")
	print(("Installed %d Mason packages: %s"):format(#package_names, table.concat(package_names, ", ")))
end

local function install_treesitter_parsers()
	local parsers = require("treesitter-parsers")
	assert(#parsers > 0, "No Treesitter parsers were requested")

	-- The second value is the error if the task failed, and otherwise whether
	-- every parser installed
	local ok, result = require("nvim-treesitter").install(parsers):pwait(treesitter_timeout_ms)
	assert(ok, "Installing Treesitter parsers failed: " .. tostring(result))
	assert(result == true, "Installing some Treesitter parsers failed, see the log above")

	-- install() leaves out unknown parsers with only a log message, and reports
	-- success for the rest, so check each parser by loading it.
	local problems = {}
	for _, parser in ipairs(parsers) do
		local loaded, added = pcall(vim.treesitter.language.add, parser)
		if not loaded or not added then
			problems[#problems + 1] = parser
		end
	end
	fail_if_any(problems, "Treesitter parsers that failed to install:")
	print(("Installed %d Treesitter parsers: %s"):format(#parsers, table.concat(parsers, ", ")))
end

require("lazy").load({ plugins = { "mason.nvim", "mason-lspconfig.nvim", "nvim-treesitter" } })

check_plugin_builds()
refresh_mason_registry()
install_mason_packages(get_requested_mason_packages())
install_treesitter_parsers()
