---
name: jira-preferences
description: User preferences for working with Jira via the Atlassian MCP. Use whenever interacting with Jira tickets — creating, editing, reading, searching, or linking issues. Applies to all Jira operations regardless of project. Triggers on any use of mcp__atlassian__ tools or when the user mentions Jira tickets, issues, or epics.
---

# Jira Workflow Preferences

## Mandatory checklist — every Jira write operation

1. **Preview before sending.** Creating → render summary + description as Markdown for user review. Editing → show a diff (added/removed/changed) per field. Wait for explicit approval before calling the MCP tool.
2. **Preserve existing content.** When updating descriptions, rewrite the full field (API requirement) but keep all existing structure, formatting, headings, links, and content that are not being changed.
3. **No scope prefixes in summaries.** Do not prefix with "UI:", "FE:", or similar. Keep summaries clean and descriptive.
4. **Use smartlinks for ticket references in descriptions.** Never use plain Markdown links (`[MIG-123](url)`) or bare keys (`MIG-123`). See smartlink format below.

## Reading tickets

Use `responseContentFormat: "markdown"` when fetching tickets.

## Smartlink format for ticket references in descriptions

| Content format | How to reference tickets |
|---|---|
| `markdown` | Full URL on its own line or inline: `https://enterprisedb.atlassian.net/browse/MIG-7921` |
| `adf` | `inlineCard` node: `{"type": "inlineCard", "attrs": {"url": "https://enterprisedb.atlassian.net/browse/MIG-7921"}}` |

In conversation with the user (outside Jira descriptions), plain text like `MIG-7921` is fine.
