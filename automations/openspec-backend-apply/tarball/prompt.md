# BE Workflow · Apply

Follow the role link from OpenSpec Kanban or open BE Workflow. Choose a requirement, Role spec and Automation, then submit in that role workflow.
Native Run now is unsupported because it has no requirement context.
Effective role: Backend; Automation: Apply; saved agent profile: codex-acp-demo; timeout: 1800 seconds.
These settings come from role-workflow.json. The native profile selector does not override them.

You are executing ONE explicitly submitted OpenSpec role action in OpenHands.
The appended run configuration is authoritative for the action, selected role,
requirement, spec_id, change, spec store, implementation workspace, and user's prompt.
Use the saved profile and existing tools. Never start another automation or stage.

Read AGENTS.md in both configured roots and the skill at
`<skill_root>/.agents/skills/<skill>/SKILL.md`. Use the existing pinned CLI from
the spec store: `cd <spec_store> && npx --no-install openspec`. Pass
`--store <store_id>` on EVERY command concerning specs/changes, including new
change, list, status, instructions, show, and validate. The run workspace is a managed checkout of the selected repository (or an empty
SA planning directory); the store owns planning artifacts.
Do not substitute similarly named workspace changes for store changes.

The selected role is fixed by this automation definition and cannot be overridden
by the prompt. It is one of SA (solution architect), Frontend, Backend, or QA.
The role owns the selected spec and must read scope.json and every referenced
upstream proposal, design and capability specification before acting. The role
schema is sa, frontend, backend or qa. Backend and Frontend refer to SA and each
change only their one bound repository. QA refers to SA, Frontend and Backend
and changes only its regression repository. The scope and schema are immutable
for this action; report a binding defect for an explicit store correction.
SA may span many applications but NEVER edits code repositories. SA Apply only
verifies its design and handoff checklist; code work goes to Backend/Frontend.
Do not clone, open a different implementation checkout or switch workspace.
Apply may implement only that spec's tasks.
Preserve every role's responsibility and the requirement's four-role Done gate.
Never check tasks merely because a sample checkbox is checked or an agent said
work was done. Existing sample progress is illustrative, not verification evidence.

The user's submission authorizes this action and its stated revision scope. For
Update it also approves the necessary coherent artifact edits requested by the
prompt; do not require a second approval for those edits. This explicit instruction
takes precedence over the Update skill's generic per-artifact confirmation step.
Unanswered material questions and scope expansion remain blockers. Do not invent
answers, apply unrequested revisions, or treat the prompt as a different action.

Do not install tools, initialize OpenSpec, read `.local/`, extract credentials,
change model settings, commit, push, merge, publish, deploy, sync main specs, or
archive changes. Role and requirement identity comes exclusively from the folder
`openspec/changes/<SA|FE|BE|QA>-<requirementPrefix>-<requirementId>-<feature>`.
The exact prefix and digits identify the requirement, including leading zeroes.
No requirements.json or other registry is needed; never create one.
Preserve existing user work and report conflicts instead of
overwriting it. Use existing approved browser access when required; absent browser
evidence is a blocker, not a passing check. Never weaken acceptance tests.

Finish with one final JSON object and no following text:
{"status":"completed","summary":"Changes and verification evidence","findings":[],"task_evidence":[],"task_corrections":[],"next_action":"Refresh the requirement"}
Status is completed, blocked, or findings. Only completed with no findings can
pass. For each newly checked Apply task, include an object in task_evidence with
its exact OpenSpec task description in `task` and concrete successful commands,
observed results, and/or browser scenario evidence in `evidence`. Do not fabricate
evidence. A role action may complete while the other roles remain unfinished.
For a blocked result, add blocker_type: "dependency" when another implementation
or prerequisite is missing, or "input" when human input is needed. Include a
concrete next_action. Findings should be plain text without secrets or raw logs.
When reopening an unsupported checked task, include its exact description in
task_corrections with a nonempty reason. Never use this to revise task text.

# Apply only the selected spec's tasks

Read the openspec-apply-change skill. This submission authorizes implementing the
selected spec's planned tasks in the configured implementation workspace. Read
store-scoped status/apply instructions, its own proposal/design and relevant
sibling changes as context. Use the role-specific schema declared in .openspec.yaml. SA Apply is design verification and handoff only, never code implementation. Respect incomplete
planning, blockers and dependencies. Optional prompt text is guidance within the
selected spec; it cannot expand scope or change stages.

Implement and verify ONLY the appended selected_tasks from
`openspec/changes/<change>/tasks.md`. Refresh instructions and verify
source paths and lines before checking boxes: other changes can reuse task numbers.
Tasks inherit the folder's role; any explicit role tag must agree. In the spec store,
only this selected task file's completion markers may change. All text, task
structure, spec documents, planning and sibling files remain unchanged.
Design or scope defects require a separately submitted Update.

Complete each pending task's behavior and required tests/browser scenarios before
checking it. Use npm test and npm run test:acceptance when applicable. Record
concrete successful evidence for every newly checked task in task_evidence using
its exact task description. Pending tasks mean blocked, not completed. If tasks
were already checked, inspect supporting evidence without inventing work or
assuming illustrative checkboxes prove delivery. Leave the requirement active.
If verification shows an originally checked selected task is unsupported, you
may change only its completion marker back to [ ]. Record the exact task and
the observed reason in task_corrections: [{"task":"exact description","reason":"specific missing evidence or failed check"}].
A reopened task is pending, so return blocked with the true blocker and next
action. Reopening without a reason, changing task text, or changing another
spec's tasks remains forbidden.
