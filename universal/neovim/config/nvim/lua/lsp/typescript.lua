-- NOTE: TypeScript 7 ships its own language server (`tsc --lsp`) and no
-- tsserver, so tsserver-based servers like vtsls cannot drive it. Use the
-- native server for TypeScript 7+ projects and vtsls for older ones.

---Directory whose node_modules contains the `typescript` package
---@param source integer|string buffer or path to search upward from
---@return string?
local function find_typescript_root(source)
	return vim.fs.root(source, function(name, path)
		return name == "node_modules" and vim.uv.fs_stat(vim.fs.joinpath(path, name, "typescript", "package.json")) ~= nil
	end)
end

---@param typescript_root string
---@return boolean
local function is_native_typescript(typescript_root)
	local package_json = vim.fn.readfile(vim.fs.joinpath(typescript_root, "node_modules/typescript/package.json"))
	local version = vim.json.decode(table.concat(package_json, "\n")).version
	return tonumber(version:match("^(%d+)%.")) >= 7
end

local vtsls_root_dir = vim.lsp.config.vtsls.root_dir

vim.lsp.config("vtsls", {
	-- NOTE: vtsls uses the same VS Code settings as the native server
	settings = vim.lsp.config.tsgo.settings,

	root_dir = function(bufnr, on_dir)
		local typescript_root = find_typescript_root(bufnr)
		if typescript_root and is_native_typescript(typescript_root) then
			return
		end

		vtsls_root_dir(bufnr, on_dir)
	end,
})

vim.lsp.config("tsgo", {
	cmd = function(dispatchers, config)
		-- NOTE: TypeScript 7 installs the native binary as `tsc`, not `tsgo`
		local tsc = vim.fs.joinpath(config.root_dir, "node_modules/.bin/tsc")
		return vim.lsp.rpc.start({ tsc, "--lsp", "--stdio" }, dispatchers)
	end,

	root_dir = function(bufnr, on_dir)
		local typescript_root = find_typescript_root(bufnr)
		if typescript_root and is_native_typescript(typescript_root) then
			on_dir(typescript_root)
		end
	end,
})

-- NOTE: enabled here instead of in the list of servers in lsp/init.lua so that
-- Mason does not install a global tsgo. The project's TypeScript is used.
vim.lsp.enable("tsgo")
