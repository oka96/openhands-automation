# Apply only the selected spec's tasks

Read the openspec-apply-change skill. This submission authorizes implementing the
selected spec's planned tasks in the configured implementation workspace. Read
store-scoped status/apply instructions, its own proposal/design and relevant
sibling changes as context. Use the role-specific schema declared in .openspec.yaml. SA Apply prepares its design handoff only, never code implementation. Respect incomplete
planning, blockers and dependencies. Optional prompt text is guidance within the
selected spec; it cannot expand scope or change stages.

Implement ONLY the appended selected_tasks from
`openspec/changes/<change>/tasks.md`. Refresh instructions and verify
source paths and lines before checking boxes: other changes can reuse task numbers.
Tasks inherit the folder's role; any explicit role tag must agree. In the spec store,
only this selected task file's completion markers may change. All text, task
structure, spec documents, planning and sibling files remain unchanged.
Design or scope defects require a separately submitted Update.

The OpenHands workflow focuses on implementation. Code validation, acceptance
checks and regression execution stay local, outside this workflow; do not run
them unless the submitted prompt explicitly requests them. QA implements the
regression code in its own repository. This boundary takes precedence over the
skill's generic instruction to run every test/browser scenario as part of Apply.
Record concrete implementation evidence for every newly checked task in
task_evidence using its exact task description. Leave validation-only tasks
unchecked and report them as pending local validation; never invent passing
results. Review and delivery do not require a test-result record. Pending tasks
mean blocked, not completed. If tasks
were already checked, inspect supporting evidence without inventing work or
assuming illustrative checkboxes prove delivery. Leave the requirement active.
If inspection shows an originally checked selected task is unsupported, you
may change only its completion marker back to [ ]. Record the exact task and
the observed reason in task_corrections: [{"task":"exact description","reason":"specific missing evidence or failed check"}].
A reopened task is pending, so return blocked with the true blocker and next
action. Reopening without a reason, changing task text, or changing another
spec's tasks remains forbidden.
