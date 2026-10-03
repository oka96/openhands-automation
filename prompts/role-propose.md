# Propose one role-owned spec

Read the openspec-propose skill for artifact guidance. This action adds a spec to
an EXISTING requirement change using the local `role-specs` schema; do not create
a new change, replace shared planning, or allocate a new requirement. Read the
requirement's proposal.md, design.md and relevant sibling specs as read-only
context. Read status and schema instructions with --store <store_id>.

Create exactly `openspec/changes/<change>/specs/<spec_id>/spec.md` and
`openspec/changes/<change>/tasks/<spec_id>.md` in the configured store. The supplied
canonical spec_id is authoritative. Draft requirement scenarios for the selected
role and feature from the prompt. Use OpenSpec delta spec requirements/scenarios
and nonempty tasks tagged only with the exact selected role, for example
[Frontend]. Every task starts unchecked; planning is not delivery evidence.

Do not edit shared proposal/design, sibling specs/tasks, application code, main
specs, or requirements.json. Validate the existing change strictly and confirm
planning is complete. The runner registers this spec under the selected role and
requirement only after successful validation. Stop at planning; report unanswered
material scope questions as blocked.
