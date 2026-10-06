Implement only this change's tasks using current store-scoped apply instructions.
In the spec store, change only tasks.md completion markers; planning edits need Update.
Check only tasks with concrete evidence; inspect existing checked tasks rather
than trusting them. Reopen unsupported tasks with reasons. Leave unrun validation
tasks unchecked. Pending tasks mean blocked; keep the change active.
