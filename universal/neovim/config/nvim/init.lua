-- NOTE: execute https://github.com/tpope/vim-sensible at the start so it does
-- not override my configuration
vim.cmd.runtime("plugin/sensible.vim")
vim.o.relativenumber = true
vim.o.number = true
vim.o.ignorecase = true
vim.o.smartcase = true
vim.o.wrap = false
vim.o.mouse = "a"
vim.o.scrolloff = 5
vim.o.sidescrolloff = 8
vim.o.cmdheight = 2
vim.o.hidden = true
vim.o.writebackup = false
vim.o.swapfile = false
vim.o.undofile = true
vim.o.signcolumn = "yes:2"

vim.o.splitbelow = true
vim.o.splitright = true

vim.o.cursorline = true
vim.o.colorcolumn = "+1,120"
vim.o.updatetime = 100

vim.o.tabstop = 2
vim.o.shiftwidth = 2
vim.o.expandtab = true

vim.opt.spell = true
vim.opt.spelloptions:append("camel")

vim.opt.path:remove("/usr/include")

vim.o.list = true
-- Source: https://github.com/tjdevries/cyclist.vim
vim.opt.listchars = {
	["tab"] = "» ",
	["trail"] = "·",
	["extends"] = "<",
	["precedes"] = ">",
	["conceal"] = "┊",
	["nbsp"] = "␣",
}

vim.o.termguicolors = true
vim.opt.diffopt:append({
	"algorithm:patience",
	"iwhite",
	"indent-heuristic",
	"vertical",
	"linematch:60",
})

vim.o.winborder = "single"

-- Mutate jumplist on longer jumps
vim.keymap.set("n", "k", [[(v:count > 5 ? "m'" . v:count : "") . 'k']], { expr = true })
vim.keymap.set("n", "j", [[(v:count > 5 ? "m'" . v:count : "") . 'j']], { expr = true })

-- Line indentation
vim.keymap.set("x", "<", "<gv", { desc = "Deindent lines" })
vim.keymap.set("x", ">", ">gv", { desc = "Indent lines" })

-- Better search and replace word under cursor
vim.keymap.set("n", "cn", "*``cgn", { desc = "Change word under cursor (repeatable forward)" })
vim.keymap.set("n", "cN", "*``cgN", { desc = "Change word under cursor (repeatable backward)" })

-- Easy yanking to clipboard
vim.keymap.set({ "n", "v" }, "<Leader>y", '"+y', { desc = "Yank to clipboard" })

if vim.fn.has("mac") then
	-- Bring back Alt-Left/Right in cmdline mode on Mac
	-- https://stackoverflow.com/a/58055423
	vim.keymap.set("c", "<M-Left>", "<S-Left>", { desc = "Move left by word" })
	vim.keymap.set("c", "<M-Right>", "<S-Right>", { desc = "Move right by word" })
end

vim.keymap.set("n", "yc", "yygccp", { desc = "Duplicate line and comment out the first one", remap = true })

-- Use ripgrep instead of regular grep (even though it's the default in Neovim
-- now, because I want to use --smart-case)
if vim.fn.executable("rg") then
	vim.o.grepprg = "rg --vimgrep --no-heading --smart-case"
	vim.o.grepformat = "%f:%l:%c:%m,%f:%l:%m"
else
	vim.fn.echoerr("rg (ripgrep) is not installed. Thus, it will not be used for :grep")
end

vim.api.nvim_create_autocmd("TextYankPost", {
	group = vim.api.nvim_create_augroup("HighlightYank", { clear = true }),
	desc = "Highlight yanked text",
	callback = function()
		vim.hl.on_yank({ higroup = "IncSearch", timeout = 300 })
	end,
})

-- Bootstrap lazy.nvim
-- https://github.com/folke/lazy.nvim#-installation
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
	vim.fn.system({
		"git",
		"clone",
		"--filter=blob:none",
		"https://github.com/folke/lazy.nvim.git",
		"--branch=stable", -- latest stable release
		lazypath,
	})
end
vim.opt.rtp:prepend(lazypath)

require("commands").setup()
require("lazy").setup("plugins", {
	change_detection = {
		enabled = false,
	},
})
