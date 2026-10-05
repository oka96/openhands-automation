# Propose one role-owned change

Read the openspec-propose skill for artifact guidance. The runner has already
created exactly `openspec/changes/<change>/` and its `.openspec.yaml` with the
role-specific schema. The supplied change equals spec_id and determines
the requirement and role. Do not run `openspec new change`: the pinned command
rejects uppercase creation names although other commands support these folders.

Read the existing context_change and relevant related_changes as read-only
requirement context. Run status and schema instructions for the NEW selected
change with --store <store_id>. Create its own proposal.md, design.md,
specs/<spec_id>/spec.md and tasks.md. Use the submitted prompt to draft observable
requirements and scenarios, plus nonempty, initially unchecked tasks. Tasks
inherit the folder's role; any explicit role tag must match it (for example,
[Frontend]). Do not create requirements.json or register the folder elsewhere.

Optional display context can be ordinary bullets in a `## Kanban` section in
proposal.md: Requirement title, Requirement summary, Spec title, Owner, Role note,
State, Note. Copy relevant requirement context only when supported by source;
State is backlog, in_progress or blocked, and never signifies completion.
This section is optional and cannot override the folder's identity.

Preserve .openspec.yaml, sibling changes, main specs and implementation files.
Validate the new change strictly and confirm planning is complete. All tasks
start unchecked. Stop at planning and report unanswered material questions as
blocked. A partial folder remains visible for a later explicit Update.
