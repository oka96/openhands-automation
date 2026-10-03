# Apply only the selected spec's tasks

Read the openspec-apply-change skill. This submission authorizes implementing the
selected spec's planned tasks in the configured implementation workspace. Read
store-scoped status/apply instructions, shared proposal/design and relevant
sibling specs as context. Use the local role-specs schema. Respect incomplete
planning, blockers and dependencies. Optional prompt text is guidance within the
selected spec; it cannot expand scope or change stages.

Implement and verify ONLY the appended selected_tasks from
`openspec/changes/<change>/tasks/<spec_id>.md`. Refresh instructions and verify
source paths and lines before checking boxes: other specs can reuse task numbers.
Every selected task must carry the exact selected role tag. In the spec store,
only this selected task file's completion markers may change. All text, task
structure, spec documents, shared planning and sibling files remain unchanged.
Design or scope defects require a separately submitted Update.

Complete each pending task's behavior and required tests/browser scenarios before
checking it. Use npm test and npm run test:acceptance when applicable. Record
concrete successful evidence for every newly checked task in task_evidence using
its exact task description. Pending tasks mean blocked, not completed. If tasks
were already checked, inspect supporting evidence without inventing work or
assuming illustrative checkboxes prove delivery. Leave the requirement active.
