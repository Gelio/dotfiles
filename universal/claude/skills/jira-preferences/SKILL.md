---
name: jira-preferences
description: User preferences for working with Jira via the Atlassian MCP. Use whenever interacting with Jira tickets — creating, editing, reading, searching, linking, commenting on, or transitioning issues, adding worklogs, or running JQL. Applies to all Jira operations regardless of project. Triggers on any use of mcp__atlassian__ tools, references to ticket keys (e.g. MIG-1234, PROJ-567), or when the user mentions Jira tickets, issues, epics, sprints, or comments.
---

# Jira Workflow Preferences

## Mandatory rules — every Jira write operation

1. **Always use ADF (`contentFormat: "adf"`) when writing a description.** Never use Markdown mode to write a description — it is lossy and can silently delete attachments (see "Failure modes" below). If you cannot avoid Markdown mode on a ticket with attachments, warn the user before writing.
2. **Preview before sending.** Creating → render summary + description as Markdown for user review. Editing → show a diff (added/removed/changed) per field. Wait for explicit approval before calling the MCP tool.
3. **Preserve existing content when editing.** Descriptions must be rewritten in full (API requirement), but keep every heading, link, formatting, and piece of content that is not being changed.
4. **No scope prefixes in summaries.** Do not prefix with `UI:`, `FE:`, `BE:`, `[Frontend]`, or similar. Keep summaries clean and descriptive.
5. **Use `inlineCard` nodes for ticket references inside descriptions.** See smartlink format below.

## Critical trap: `getJiraIssue` cannot return ADF

`getJiraIssue` returns Markdown even when called with `responseContentFormat: "adf"`. You cannot fetch ADF to splice into an edit. When editing a description, you **must reconstruct the ADF document manually** from the Markdown you fetched plus the changes you're making. Do not fall back to Markdown writes to avoid this work — that triggers the failure modes below.

## Reading tickets

Use `responseContentFormat: "markdown"` when fetching tickets (ADF isn't available anyway).

## Smartlink format for ticket references in descriptions

Always use an `inlineCard` node (ADF mode is required, per rule 1):

```json
{"type": "inlineCard", "attrs": {"url": "https://enterprisedb.atlassian.net/browse/MIG-7921"}}
```

In conversation with the user (outside Jira descriptions), plain text like `MIG-7921` is fine.

## Integrated example — edit a description

User: "Add a 'Testing' section to MIG-1234 with a link to MIG-7921."

1. **Fetch** the current description with `getJiraIssue` (`responseContentFormat: "markdown"`). You get Markdown back — not ADF — per the trap above.
2. **Reconstruct ADF manually.** Build an ADF `doc` whose `content` preserves every heading, paragraph, list, and link from the fetched Markdown verbatim, then append the new section as ADF nodes. Do not drop or paraphrase existing content.
3. **Preview the diff to the user.** Show only the added/changed sections and confirm nothing upstream was lost.
4. **Wait for explicit approval.**
5. **Call `editJiraIssue`** with `contentFormat: "adf"` and the reconstructed document as the description field.

Minimal ADF skeleton for the appended section in step 2:

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    { "type": "heading", "attrs": { "level": 2 }, "content": [{ "type": "text", "text": "Testing" }] },
    { "type": "paragraph", "content": [
      { "type": "text", "text": "See " },
      { "type": "inlineCard", "attrs": { "url": "https://enterprisedb.atlassian.net/browse/MIG-7921" } }
    ]}
  ]
}
```

## Failure modes of Markdown mode (all confirmed, not theoretical)

- **Bare URLs do not reliably render as inline cards / smart links.** Only `inlineCard` ADF nodes do. Bare Jira ticket URLs in Markdown usually render as plain text.
- **Link text containing inline code gets stripped.** `` [`Foo`](url) `` loses the link entirely — the URL disappears.
- **Bold wrappers that start with inline code collapse.** `` **`q` (...)** `` renders as plain text, losing the bold.
- **`![](filename.png)` does NOT resolve to an existing attachment.** Jira re-serializes it as a malformed `blob:` URL that never renders.
- **Attachments not referenced by media id in the new description are deleted.** Jira garbage-collects them on write. The Atlassian MCP exposes no attachment-upload tool, so this is effectively data loss with no programmatic recovery.
