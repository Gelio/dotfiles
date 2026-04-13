---
name: enrich-todos
description: Annotate a TODO/review-feedback file with context from the current conversation to help the next agent implement the items. Use when the user says "add context to TODOs", "enrich TODOs", "annotate TODOs for the next agent", "add implementation hints", or asks you to look at a todos/impl-todos file and add what you know. Also triggers when the user asks to prepare handoff notes for remaining work after completing an implementation session.
argument-hint: '<path-to-todos.md>'
---

# Enrich TODOs with Conversation Context

## Hard constraints

1. **No research.** Do not read files, grep, or search. Use only what is already in your conversation context. The value is speed, not completeness.
2. **Do not pad.** Skip TODO items where you have nothing specific to add. A note that restates the TODO in different words is worse than no note.
3. **Preserve existing text.** Do not reorder, reword, or remove existing items. Do not mark items as done. Only add `**Context:**` notes.

## Process

1. Read the TODO file at `$0`. If not provided, look for
   `impl-todos.md` or `todos.md` in `agent-plans/` or the current
   directory. Ask if ambiguous.

2. For each TODO item, decide: do you have **specific, non-obvious
   context** from this conversation that would save the next agent
   2+ tool calls? If yes, append a `**Context:**` paragraph directly
   below the item, indented to match. If no, move on.

   Useful context includes:
   - File paths and line numbers of related code
   - Type names, function signatures, import paths
   - Patterns to follow (with the file that demonstrates them)
   - Ticket/issue references
   - Gotchas encountered during implementation
   - DOM structure or accessibility details from test debugging

3. Edit the TODO file in place.

## Example

Before:
```markdown
- [ ] Add error handling to the delete mutation
- [ ] Rename `oldVar` to `newVar`
- [ ] Add e2e test for the new filter dropdown
```

After:
```markdown
- [ ] Add error handling to the delete mutation
  **Context:** `useIdpDeleteAction` (`onprem/ui/src/components/IdentityProviders/actions/useIdpDeleteAction.tsx`) shows the pattern: wrap the mutation's `onError` with `errorHandler` from `@/utils/errorHandler.ts`. The delete endpoint returns `409` when the resource is in use — handle that with a specific toast (see `useDeleteCluster.tsx:47`).
- [ ] Rename `oldVar` to `newVar`
- [ ] Add e2e test for the new filter dropdown
  **Context:** The dropdown renders inside `data-testid="status-filter"`. Use `page.getByTestId('status-filter').getByRole('combobox')` — `getByRole('combobox')` alone matches multiple elements. See `onprem/e2e/tests/clusters/clusterList.spec.ts:82` for a similar filter test.
```

The "Rename" item was skipped — the next agent needs no extra context for that.
