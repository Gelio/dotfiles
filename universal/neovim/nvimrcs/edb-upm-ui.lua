local augroup = vim.api.nvim_create_augroup("Customizations", {})

vim.api.nvim_create_autocmd("FileType", {
  pattern = "markdown",
  group = augroup,
  callback = function()
    vim.wo.wrap = true
    vim.wo.linebreak = true
  end,
})

vim.api.nvim_create_user_command("Tsc", "Dispatch -compiler=tsc NO_COLOR=1 npm run tsc", {
  desc = "Run TypeScript compiler and put the results in the quickfix list",
})

local tsserver_lsp = require("lsp.tsserver")

-- Root of the repository
local nvimrc_path = vim.fn.expand("<script>:h")
tsserver_lsp.setup(vim.tbl_extend("force", tsserver_lsp.config, {
  settings = {
    tsserver_file_preferences = {
      quotePreference = "single",
    },
  },
  root_dir = function()
    return nvimrc_path
  end,
}))

---@return string|nil
local function find_closest_package_path()
  -- Find the closest package.json from the current buffer, but stop at the repository root
  local closest_package_json_path = vim.fn.findfile("package.json", ".;" .. nvimrc_path)
  if closest_package_json_path == "" then
    error(string.format("No package.json found from %s", vim.api.nvim_buf_get_name(0)))
  end

  local closest_package_path = vim.fn.fnamemodify(closest_package_json_path, ":h")

  return closest_package_path
end

---@type string[]
local npm_workspaces = {}

local function run_eslint(params)
  local package_path = params.fargs[1]
  if package_path ~= nil then
    if not vim.tbl_contains(npm_workspaces, package_path) then
      error(string.format('Unknown npm workspace path "%s"', package_path))
    end
  else
    local closest_package_path = find_closest_package_path()
    if closest_package_path == nil then
      return
    end
    package_path = closest_package_path
  end

  vim.cmd.Dispatch({
    "-compiler=eslint",
    "-dir=" .. package_path,
    "npx",
    "eslint",
    "--format",
    "compact",
    "--cache",
    ".",
  })
end

vim.api.nvim_create_user_command("Eslint", run_eslint, {
  desc = "Run ESLint and put the results in the quickfix list",
  nargs = "?",
  complete = function()
    return npm_workspaces
  end,
})

local function get_npm_workspaces()
  local Job = require("plenary.job")

  Job:new({
    command = "npm",
    args = { "query", ".workspace" },
    cwd = nvimrc_path,
    on_exit = function(job)
      local workspaces = vim.json.decode(table.concat(job:result(), "\n"))

      local workspace_locations = vim.tbl_map(function(workspace)
        return workspace.location
      end, workspaces)

      npm_workspaces = workspace_locations
    end,
  }):start()
end

get_npm_workspaces()
