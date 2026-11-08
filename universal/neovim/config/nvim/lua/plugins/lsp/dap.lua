return {
	{
		"mfussenegger/nvim-dap",
		keys = {
			{ "<Leader>xb", "<cmd>DapToggleBreakpoint<CR>", desc = "Toggle breakpoint" },
			{ "<Leader>xc", "<cmd>DapContinue<CR>", desc = "Continue" },
			{ "<Leader>xso", "<cmd>DapStepOut<CR>", desc = "Step out" },
			{ "<Leader>xsn", "<cmd>DapStepOver<CR>", desc = "Step over" },
			{ "<Leader>xsi", "<cmd>DapStepInto<CR>", desc = "Step into" },
			{ "<Leader>xsc", "<cmd>DapRunToCursor<CR>", desc = "Run to cursor" },
		},
		cmd = { "DapToggleBreakpoint", "DapContinue" },
		init = function()
			require("which-key").add({
				{ "<Leader>x", group = "Dap (debug)" },
			})
		end,
		config = function()
			local dap = require("dap")
			local create_command = vim.api.nvim_create_user_command
			local utils = require("utils")

			-- TODO: support adding logpoints and conditional breakpoints
			create_command("DapToggleBreakpoint", utils.execute_function_without_args(dap.toggle_breakpoint), {})
			create_command("DapContinue", utils.execute_function_without_args(dap.continue), {})
			create_command("DapStepOver", utils.execute_function_without_args(dap.step_over), {})
			create_command("DapStepInto", utils.execute_function_without_args(dap.step_into), {})
			create_command("DapStepOut", utils.execute_function_without_args(dap.step_out), {})
			create_command("DapTerminate", utils.execute_function_without_args(dap.terminate), {})
			create_command("DapRunToCursor", utils.execute_function_without_args(dap.run_to_cursor), {})
			create_command("DapReplOpen", utils.execute_function_without_args(dap.repl.open), {})
			create_command("DapReplToggle", utils.execute_function_without_args(dap.repl.toggle), {})
			create_command("DapReplClose", utils.execute_function_without_args(dap.repl.close), {})
			create_command("DapStatus", function()
				print(dap.status())
			end, {})
		end,
	},
	{
		"rcarriga/nvim-dap-ui",
		keys = {
			{ "<Leader>xK", "<cmd>DapUIEval<CR>", desc = "Evaluate expression under cursor" },
			{ "<Leader>xx", "<cmd>DapUI<CR>", desc = "Toggle Dap UI" },
		},
		cmd = { "DapUIOpen", "DapUI", "DapUIEval" },
		dependencies = { "nvim-dap", "nvim-neotest/nvim-nio" },
		config = function()
			local dapui = require("dapui")
			dapui.setup()

			local create_command = vim.api.nvim_create_user_command
			local utils = require("utils")

			create_command("DapUIOpen", utils.execute_function_without_args(dapui.open), {})
			create_command("DapUIClose", utils.execute_function_without_args(dapui.close), {})
			create_command("DapUI", utils.execute_function_without_args(dapui.toggle), {})
			create_command("DapUIEval", function(args)
				dapui.eval(string.len(args.args) > 0 and args.args or nil)
			end, {
				nargs = "?",
			})
		end,
	},
}
