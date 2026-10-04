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
	-- Like kitty's ctrl+shift+p hints prefix, see config.key_tables.hints
	{ key = "p", mods = "CTRL|SHIFT", action = act.ActivateKeyTable({ name = "hints", one_shot = true }) },
	-- Searchable emoji and Unicode picker
	{ key = "u", mods = "CTRL|SHIFT", action = act.CharSelect },
	-- Like kitty's default URL hints (ctrl+shift+e): pick a URL and open it in the browser
	{
		key = "e",
		mods = "CTRL|SHIFT",
		action = act.QuickSelectArgs({
			label = "open url",
			patterns = { "https?://\\S+" },
			skip_action_on_paste = true,
			action = wezterm.action_callback(function(window, pane)
				wezterm.open_with(window:get_selection_text_for_pane(pane))
			end),
		}),
	},
}

-- Quick Select labels matches on screen. Type a label to copy it (uppercase label also pastes)
config.key_tables = {
	hints = {
		-- Paths, URLs, hashes and the other default patterns
		{ key = "f", action = act.QuickSelect },
		-- Words, using kitty's default word characters and minimum length
		{
			key = "w",
			action = act.QuickSelectArgs({
				label = "copy word",
				patterns = { "[\\w@./~?&=%+#-]{3,}" },
			}),
		},
		-- ctrl+shift+p was the command palette before it became the hints prefix
		{ key = "p", action = act.ActivateCommandPalette },
	},
}

if is_windows then
	-- Open the default WSL distro in its home directory
	config.default_prog = { "wsl.exe", "--cd", "~" }
end

return config
