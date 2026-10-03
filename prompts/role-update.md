# Update one role-owned spec

Read the openspec-update-change skill and the requirement's shared proposal,
design and sibling specs as read-only context. Revise only
`openspec/changes/<change>/specs/<spec_id>/spec.md` and
`openspec/changes/<change>/tasks/<spec_id>.md` coherently from the submitted prompt.
The selected spec, role and requirement are fixed. Submission authorizes the
necessary scoped artifact edits; no generic per-artifact approval is needed.

Keep a nonempty task set tagged only with the selected role. Preserve completed
tasks and evidence unless the revision explicitly invalidates them; explain
reopened tasks. Never newly check tasks or transfer completion to revised text.
Shared proposal/design, siblings, application code, requirements.json and main
specs must remain unchanged. If the request needs changes beyond this spec or
material unanswered decisions, report the blocker instead of expanding scope.

Run strict validation of the requirement change and confirm planning is complete.
Stop after planning; never run Apply or another action automatically.
