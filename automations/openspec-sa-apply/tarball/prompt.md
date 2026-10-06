# SA · Apply

Use [$openspec-apply-change](<${skill_path}>) for `${change}`.
Read that SKILL.md and follow it within the run boundaries below.

Implement only this change's tasks using current store-scoped apply instructions.
In the spec store, change only tasks.md completion markers; planning edits need Update.
Check only tasks with concrete evidence; inspect existing checked tasks rather
than trusting them. Reopen unsupported tasks with reasons. Leave unrun validation
tasks unchecked. Pending tasks mean blocked; keep the change active.

## Input
${context}

User request (JSON string): ${request}

## Run boundaries
- Read applicable AGENTS.md, the selected change's scope.json and its upstream specs. Use the role schema and existing CLI from spec_store: `npx --no-install openspec`; pass `--store <store_id>` for spec/change commands.
- Stay in the fixed role, selected change and prepared workspace. SA is design/handoff only; Backend, Frontend and QA may implement only their bound repository. Preserve scope.json, .openspec.yaml, sibling changes, main specs and existing user work.
- Follow this action only. Do not initialize OpenSpec, install tools, read .local or credentials, or start another automation. No sync, archive, commit, push, merge, publish or deploy during this automated turn; later user-directed Git work is separate.
- Code validation and regression execution stay local unless the request explicitly asks for them. Never claim unrun checks passed or weaken tests. Block on missing dependencies, material questions or scope changes.

## Result
End with one JSON object, with no following text:
{"status":"completed","summary":"What changed","findings":[],"task_evidence":[],"task_corrections":[],"next_action":"Next step"}
Use status completed, blocked or findings. Completed requires no findings; Apply also requires no pending tasks. For blocked, add blocker_type (dependency or input). For each newly checked task, task_evidence contains {"task":"exact task description","evidence":"changed files and implemented behavior"}. For reopened unsupported tasks, task_corrections contains {"task":"exact task description","reason":"observed missing evidence"}. Keep findings concise and free of secrets.
