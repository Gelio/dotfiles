local wezterm = require("wezterm")
local act = wezterm.action

local config = wezterm.config_builder()
local is_windows = wezterm.target_triple:find("windows") ~= nil

config.font = wezterm.font("JetBrainsMono Nerd Font Mono")
config.font_size = 13.0
-- Make the underline thicker to better see contexts in Neovim
config.underline_thickness = "125%"

config.color_scheme = "Dracula (Official)"

config.audible_bell = "Disabled"
-- No title bar, but keep the borders so the window can still be resized
config.window_decorations = "RESIZE"
config.window_padding = { left = 0, right = 0, top = 0, bottom = 0 }
-- Do not ask for confirmation when closing a window.
-- It often prevents restart/shutting down the system when the terminal is open
config.window_close_confirmation = "NeverPrompt"

-- tmux handles splits and windows
config.enable_tab_bar = false

-- Do not grab keys that are used in tmux and Neovim (e.g. <C-S-W>, <C-S-F>, <C-S-B>)
config.disable_default_key_bindings = true
config.keys = {
	{ key = "c", mods = "CTRL|SHIFT", action = act.CopyTo("Clipboard") },
	{ key = "v", mods = "CTRL|SHIFT", action = act.PasteFrom("Clipboard") },
	{ key = "phys:Equal", mods = "CTRL|SHIFT", action = act.IncreaseFontSize },
	{ key = "phys:Minus", mods = "CTRL|SHIFT", action = act.DecreaseFontSize },
	{ key = "Backspace", mods = "CTRL|SHIFT", action = act.ResetFontSize },
	{ key = "r", mods = "CTRL|SHIFT", action = act.ReloadConfiguration },
	{ key = "l", mods = "CTRL|SHIFT", action = act.ShowDebugOverlay },
	{ key = "p", mods = "CTRL|SHIFT", action = act.ActivateCommandPalette },
}

if is_windows then
	-- Open the default WSL distro in its home directory
	config.default_prog = { "wsl.exe", "--cd", "~" }
end

return config
