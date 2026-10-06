# Apply approved planning artifacts

The human manually selected Apply for the configured change. This is the explicit
implementation request after review of its current planning artifacts. It grants
no approval to broaden scope, sync main specs, archive, commit, push, or deploy.

Read `.agents/skills/openspec-apply-change/SKILL.md`. Read the proposal, delta specs,
design, tasks, and current pinned CLI apply instructions before editing code.
Run `npm run spec:validate` and
`npx --no-install openspec instructions apply --change <configured-change> --json`.
Stop if planning artifacts are incomplete or contradictory.

Implement pending tasks and preserve existing behavior. If all tasks are already
complete, inspect them and report that state without inventing work. A newly found
defect outside the current tasks should be reported for Update, not silently folded
into this change. Check each task only after its implementation or verification
actually succeeds. Run `npm test`, `npm run test:acceptance`, and required browser
scenarios. Report missing evidence honestly. Leave the change active.

Return changed files and validation evidence. Recommend the independent Verify
stage next; do not claim independent review has happened in this conversation.
