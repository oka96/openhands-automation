# Propose a new requirement

Read the openspec-propose skill. The selected existing requirement is context,
not the destination. Read its artifacts and inspect relevant application code
read-only. Create the supplied distinct unused `change` in the configured store
using `new change --store <store_id>` and the pinned schema instructions.

Draft proposal, scenarios, design, and tasks from the single user prompt through
the selected role's perspective. Plan the whole requirement with nonempty task
sets explicitly tagged [SA], [Frontend], [Backend], and [QA]. Every task starts
unchecked; planning alone does not complete delivery work. Do not implement any
application code or edit the context requirement, main specs, or existing changes.

Run strict validation on the new change and confirm complete planning artifacts.
Stop at planning. The runner adds a new requirement record, with a stable new ID
and all four roles, only after successful validation. Leave all other metadata
untouched. Report missing requirements or unanswered material questions as blocked.
