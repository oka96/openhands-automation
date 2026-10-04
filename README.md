# OpenSpec stages in OpenHands

Run **Propose**, **Update**, or **Apply** for SA, Frontend, Backend, or QA from the
requirement board in `/Users/oka/Desktop/openhands-apps`. Select a requirement,
role, spec, and action, enter one prompt, and submit. OpenHands starts one native
automation run with a linked conversation and visible result. Definitions and
runtime code live here; the App dispatches them through a signed local event.

There are twelve dedicated automations. Each role (SA, Frontend, Backend, QA) has
its own Propose, Update and Apply definition, named `OpenSpec <role> · <skill>`.
The seven legacy stage definitions and three generic role definitions are retired.

## Role actions

| Action | User input | Result and boundary |
| --- | --- | --- |
| OpenSpec <role> · Propose | Role, new feature slug, prompt | Add one named spec and task file to the selected requirement; no implementation |
| OpenSpec <role> · Update | Role, existing spec and revision prompt | Revise only that spec and its task planning; no implementation |
| OpenSpec <role> · Apply | Role, existing spec and optional guidance prompt | Implement and verify only that spec’s tasks; preserve siblings |

Submitting Update explicitly approves artifact edits needed for the stated
revision within the selected spec. Submitting Apply authorizes implementation of that spec's current
planned tasks. Unanswered material questions and changes outside that scope stop
the run. Completion never launches another action. Done on the board still
requires SA, Frontend, Backend, and QA to finish.

Examples: SA → Propose → `Plan task attachments with size limits and clear failure
states`; Frontend → Update → `Clarify keyboard focus after a failed save`;
Backend → Apply → `Follow the existing built-in HTTP conventions`; QA → Apply →
`Verify keyboard and failed-request scenarios`. Any of the four roles can submit
any of the three actions. Each requirement can contain several specs per role.
Propose uses a feature slug such as `date-validation` to derive a canonical ID:
`SA-REQ-002-date-validation`, `FE-REQ-002-date-validation`,
`BE-REQ-002-date-validation`, or `QA-REQ-002-date-validation`. It creates tasks only
for the selected role. At most 20 specs can be registered per requirement.

The fixed deployment configuration is `role-workflow.json`. Kanban displays its
effective Role, mapped OpenSpec skill, saved agent profile, implementation project,
spec store, skill source and timeout. Reconnect after editing configuration or
rebuilding bundles. Each native bundle's `prompt.md` also explains its launch
path and fixed profile; the native profile selector does not override these
role runners.

```json
{
  "workspace": "/Users/oka/Desktop/openhands-demo",
  "spec_store": "/Users/oka/Desktop/openspec-store",
  "store_id": "openspec-store",
  "skill_root": "/Users/oka/Desktop/openhands-demo",
  "profile": "codex-acp-demo",
  "timeout_seconds": 1800,
  "canvas_url": "http://127.0.0.1:8000"
}
```

The workspace receives implementation changes; the registered store owns the
planning artifacts in independently scoped role change folders. Existing project-local
OpenSpec skills are read from `skill_root`; no replacement skills are installed.
The runner uses the pinned `npx --no-install openspec` CLI with an explicit
`--store openspec-store` for all change operations. A missing or mismatched store
registration blocks dispatch.

Install/connect the twelve dedicated role automations from the board's automation setup
action, then submit a role action from a requirement. A role automation's ordinary
zero-input **Run** is intentionally rejected because it lacks a role and request
context. Setup, refresh, and status checks never start an agent.

### Results and task corrections

Kanban shows business outcomes independently from native lifecycle: Completed,
Waiting for dependency, Blocked (action needed), Needs review, or Execution error.
Agents report `blocker_type: "dependency"` or `"input"` for a blocked result and
a concrete `next_action`. Findings and confirmation pauses require review;
transport, malformed results and audit errors are execution errors. Native
callbacks still use the supported COMPLETED/FAILED values.

Apply may reopen an originally checked selected task only when `task_corrections`
contains its exact description and a nonempty `reason`. This corrects unsupported
illustrative completion without changing task text, structure or siblings. Newly
completed tasks still require `task_evidence`; pending corrected tasks prevent
completion. Postflight errors preserve the original agent result alongside
specific `audit_errors` rather than replacing its blocker with a generic message.

The runner atomically records a bounded, credential-redacted result in
`~/.openhands/apps/openspec-progress/role-results/<run UUID>.json` before its
completion callback. The bridge checks its run/conversation/role/store bindings
and exposes only validated display fields and the run's captured configuration.
Native lifecycle remains authoritative. Older runs, unavailable reports and
inconsistent records retain native status with a link to the original history;
existing histories are not rewritten. Full agent diagnostics remain in run logs.

New role conversations carry exactly six native tags: `requirement` (for example,
`REQ-006`), `role` (`SA`, `Frontend`, `Backend`, or `QA`), `openspecstage` (such as
`apply`), `openspecspec` (the canonical spec ID), `automationrunid`, and
`automationtrigger`. Future role and legacy runs omit `openspecchange` and
`openspecskill`; legacy runs retain their stage and automation origin tags.

New conversation names use the plain spec ID, for example
`SA-REQ-002-date-validation` or `BE-REQ-002-date-validation`.
The runner saves the title before starting the queued agent message and disables
automatic title generation. Existing conversation metadata can be normalized
through the native API by removing a leading bracketed role prefix and only the
two obsolete tag keys, preserving other tags, messages, and run history.

Use one local OpenHands launcher for the shared automation database. Multiple
launchers on different ports can share the SQLite queue while keeping packages
in different storage directories; a competing dispatcher can then fail with a
missing tarball. Browser and desktop clients should connect to the same backend.

Requirements are compiled directly from `openspec/changes/` directory names:
`<SA|FE|BE|QA>-<PREFIX>-<digits>-<feature>`, for example
`FE-REQ-003-filters` or `BE-STORY-12-api`. Prefixes contain uppercase letters and
digits, start with a letter, and have no hyphens; feature names are lowercase
kebab-case. The exact prefix and digits identify the requirement, preserving
leading zeroes. A canonical folder name is at most 160 characters. The store
supports 50 requirements, 20 role changes per requirement and 500 tasks per group.
Archive and unrelated OpenSpec changes are excluded. No requirement registry is
read or written, including `requirements.json`.

Each role change uses standard `spec-driven` artifacts: `.openspec.yaml`,
`proposal.md`, `design.md`, `specs/<capability>/spec.md` and `tasks.md`.
Propose safely creates the new exact folder and schema file while holding both
locks; the agent supplies its planning artifacts with unchecked tasks. This
avoids the pinned CLI's lowercase-only `new change` restriction. Existing-folder
CLI operations support the canonical uppercase names. Refresh discovers the
result directly. Partial planning remains visible and an explicit Update can
repair it. Sibling changes provide read-only requirement context.

Optional `## Kanban` bullets in proposal.md can supply Requirement title,
Requirement summary, Spec title, Owner, Role note, State and Note. These display
fields never determine identity or completion. Untagged tasks inherit the folder
role; explicit task role tags must match it.

Role requests use source `openspec-role-dashboard`, schema
`openspec-role-dashboard/v3`, and event type `<stage>.requested`. The exact event
fields are `schema`, `type`, `stage`, `approval`, `request_id`, `spec_store`,
`requirement_id`, `context_change`, `role`, `spec_id`, `change`, and `request`. Prompt text
cannot override configured workspace, store, skill root, profile, or timeout.
OpenHands delivers custom webhooks as an exact three-field wrapper:
`{"payload": <signed request>, "source_override": "openspec-role-dashboard",
"event_key": "<stage>.requested"}`. The runner validates this routing metadata
before unwrapping the request; raw request delivery remains supported. Unknown
wrapper fields, wrong sources, and mismatched event keys are rejected.
Propose and Update require a prompt of at most 10,000 characters; Apply may omit
guidance. `change` always equals the canonical `spec_id`. Update and Apply also
require `context_change` to equal that existing folder. Propose requires an unused
target and an existing context change from the same requirement (any role).
Current folders are rechecked before dispatch; old v2 events are rejected.

The runner checks the envelope before mutable preflight, locks both store and
workspace, and consumes each request UUID at most once. It preserves saved
conversation confirmation/security settings and sends normal lifecycle callbacks.
After the agent finishes, it audits file scope and validates the change using
OpenSpec. Propose and Update may edit only the selected change's proposal, design,
capability specs and tasks; schema configuration, sibling changes, main specs and
implementation files must remain unchanged. Apply may only change its selected
change's task checkboxes in the store and must supply concrete
verification evidence for newly checked tasks. An invalid scope change produces
a failed run and keeps files available for inspection; it does not silently undo
user work. These audits and prompts are workflow controls, not an OS sandbox.

Bundles live in `automations/openspec-<role>-<stage>` with lowercase folder names,
for example `openspec-backend-apply`. Each contains the shared standalone runtime,
stage prompt, and immutable role/stage configuration. Signed event filters match
both role and stage; the runtime independently rejects cross-role requests.

These definitions target the existing local demo:

- Workspace: `/Users/oka/Desktop/openhands-demo`
- OpenHands Canvas: `http://127.0.0.1:8000`
- Saved agent profile: `codex-acp-demo`
- Spec store: `/Users/oka/Desktop/openspec-store`

The automation runner uses OpenHands Agent Server to start a conversation with
that saved profile. With the current profile, Codex ACP performs the agent work;
OpenHands manages dispatch, conversations, logs, and run status.

## Build and verify

Edit `role-workflow.json`, `prompts/role-*.md`, and `runtime/run.py`, then run:

```sh
npm run build
npm test
npm run check
```

The generator emits exactly twelve bundles and refuses unexpected definitions in
`automations/`. Reconnect from the board after rebuilding. Setup updates existing
pair IDs and v2 event filters, preserves the signing source, and never starts a
conversation. Reconnect after migrating a store and upgrading these bundles;
obsolete v1 events are rejected.

## Migration from the legacy definitions

Explicit Connect soft-deletes the seven recognized numbered stages and three
`OpenSpec Role` definitions, after checking that none has pending or running work.
It leaves unrelated definitions and stored conversation/run records untouched.
Connection state upgrades from stage keys to role/stage keys while retaining the
same signing secret. Interrupted uploads/installations are journaled for recovery.

The exact retired source bundles are backed up in
`archive/2026-10-04-superseded-automations.tar.gz`, outside the Git Sync folder.
Historical documentation is in `archive/legacy-workflow.md`. The old runtime test
cases remain as compatibility coverage; legacy bundles are no longer generated.
Do not restore the archive into `automations/` alongside the new definitions.

Git Sync should use this repository's `automations/` folder. Commit and push only
when requested, then sync explicitly; syncing an older remote revision can
reintroduce obsolete definitions. This local migration does not push or sync Git.
