return {
	settings = {
		basedpyright = {
			-- NOTE: ruff owns import organizing (and linting/formatting); let
			-- basedpyright focus on type checking, completion and navigation.
			disableOrganizeImports = true,
			analysis = {
				-- Report type errors across the whole project, not just open
				-- buffers. Heavier on large repos; switch to "openFilesOnly" if
				-- it gets slow.
				diagnosticMode = "workspace",
				inlayHints = {
					variableTypes = true,
					functionReturnTypes = true,
					callArgumentNames = true,
				},
			},
		},
	},
}
