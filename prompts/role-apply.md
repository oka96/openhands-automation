# Apply only the selected role's tasks

Read the openspec-apply-change skill. The submitted Apply action explicitly
authorizes implementing the selected role's planned tasks in the configured
implementation workspace. Read all proposal, design, spec, and task context
returned by store-scoped status and apply instructions. Respect blocked planning
or unresolved dependencies. Use optional prompt text as guidance within this
role's tasks, never as permission to expand scope or change stages.

Implement and verify ONLY tasks whose descriptions contain the exact selected
role tag. The appended selected_tasks contains this set; refresh instructions and
verify current source lines before checking boxes. Other roles' tasks may inform
dependencies but must remain unchanged. Preserve all task text and structure;
in the spec store, only this change's tasks.md checkboxes for the selected role
may change. Design or scope defects require a separately submitted Update.

For every selected pending task, complete its behavior and required verification
before checking it. Run relevant tests and all required acceptance/browser
scenarios; use npm test and npm run test:acceptance when applicable. Record real
verification evidence per newly checked task in task_evidence. If any selected
task remains pending, return blocked with remaining work; do not claim completed.
If selected tasks were already checked, inspect their supporting evidence and
report that state without inventing work or treating illustrative checkboxes as
proof. Leave all other roles untouched and the change active.
