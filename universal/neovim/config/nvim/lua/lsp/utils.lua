local M = {}

---@param _client vim.lsp.Client
---@param bufnr number
local function setup_lsp_keymaps(_client, bufnr)
	local function signature_help()
		vim.lsp.buf.signature_help()
	end

	require("which-key").add(vim.tbl_map(function(mapping)
		return vim.tbl_extend("force", mapping, { buffer = bufnr })
	end, {
		{
			"K",
			function()
				vim.lsp.buf.hover()
			end,
			desc = "Hover",
		},
		{ "gD", "<cmd>lua vim.lsp.buf.declaration()<CR>", desc = "Go to declaration" },
		{ "gd", "<cmd>lua vim.lsp.buf.definition()<CR>", desc = "Go to definition" },
		{ "gri", "<cmd>lua vim.lsp.buf.implementation()<CR>", desc = "Go to implementation" },
		{ "grr", "<cmd>lua vim.lsp.buf.references()<CR>", desc = "Go to references" },
		{ "g<leader>c", group = "Call hierarchy" },
		{ "g<leader>ci", "<cmd>lua vim.lsp.buf.incoming_calls()<CR>", desc = "Go to incoming calls" },
		{ "g<leader>co", "<cmd>lua vim.lsp.buf.outgoing_calls()<CR>", desc = "Go to outgoing calls" },
		{ "g<leader>t", "<cmd>lua vim.lsp.buf.type_definition()<CR>", desc = "Go to type definition" },

		{ "<C-W>gd", "<cmd>tab split | norm gd<CR>", desc = "Go to definition in a new tab" },

		{ "grn", "<cmd>lua vim.lsp.buf.rename()<CR>", desc = "Rename" },
		{ "gra", "<cmd>lua vim.lsp.buf.code_action()<CR>", desc = "Code actions", mode = { "v", "n" } },
		{ "<Leader>q", "<cmd>lua vim.diagnostic.setloclist()<CR>", desc = "Show diagnostics in location list" },

		{ "<C-k>", signature_help, desc = "Show signature help" },
		{ "<C-j>", signature_help, desc = "Show signature help", mode = "i" },
	}))
end

function M.setup_document_highlight()
	local lsp_attach_autocmd = vim.api.nvim_create_augroup("LSPDocumentHighlightAttachDetach", { clear = true })
	local document_highlight_autocmd = vim.api.nvim_create_augroup("LSPDocumentHighlight", { clear = true })
	local supported_clients_count_variable_name = "lsp_document_highlight_supported_clients_count"

	local function register_document_highlight_autocmds()
		vim.api.nvim_create_autocmd("CursorHold", {
			group = document_highlight_autocmd,
			buffer = 0,
			callback = function()
				vim.lsp.buf.document_highlight()
			end,
		})
		vim.api.nvim_create_autocmd("CursorMoved", {
			group = document_highlight_autocmd,
			buffer = 0,
			callback = function()
				vim.lsp.buf.clear_references()
			end,
		})
	end

	vim.api.nvim_create_autocmd("LspAttach", {
		group = lsp_attach_autocmd,
		callback = function(event)
			local client = vim.lsp.get_client_by_id(event.data.client_id)
			if client and client:supports_method("textDocument/documentHighlight") then
				vim.b[supported_clients_count_variable_name] = (vim.b[supported_clients_count_variable_name] or 0) + 1

				if vim.b[supported_clients_count_variable_name] == 1 then
					register_document_highlight_autocmds()
				end
			end
		end,
	})
	vim.api.nvim_create_autocmd("LspDetach", {
		group = lsp_attach_autocmd,
		callback = function(event)
			local client = vim.lsp.get_client_by_id(event.data.client_id)
			if
				client
				and client:supports_method("textDocument/documentHighlight")
				and vim.b[supported_clients_count_variable_name] ~= nil
			then
				if vim.b[supported_clients_count_variable_name] == 1 then
					vim.b[supported_clients_count_variable_name] = nil
					vim.api.nvim_clear_autocmds({ group = document_highlight_autocmd })
					vim.lsp.buf.clear_references()
				else
					vim.b[supported_clients_count_variable_name] = vim.b[supported_clients_count_variable_name] - 1
					vim.lsp.buf.document_highlight()
				end
			end
		end,
	})
end

---@param client vim.lsp.Client
---@param bufnr number
function M.on_attach(client, bufnr)
	setup_lsp_keymaps(client, bufnr)
end

-- https://cmp.saghen.dev/installation.html
local ok, cmp_capabilities = pcall(function()
	return require("blink.cmp").get_lsp_capabilities()
end)
if ok then
	M.capabilities = cmp_capabilities
else
	vim.print("Warning: Failed to load blink.cmp capabilities for LSP")
end

-- https://github.com/kevinhwang91/nvim-ufo#minimal-configuration
M.capabilities = vim.tbl_deep_extend("force", M.capabilities or {}, {
	textDocument = {
		foldingRange = {
			dynamicRegistration = false,
			lineFoldingOnly = true,
		},
	},
})

-- Base config for LSP's setup method
M.base_config = {
	on_attach = M.on_attach,
	capabilities = M.capabilities,
}

return M
