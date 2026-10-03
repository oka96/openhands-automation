# OpenSpec stages in OpenHands

Run **Propose**, **Update**, or **Apply** for SA, Frontend, Backend, or QA from the
requirement board in `/Users/oka/Desktop/openhands-apps`. Select a requirement,
role, and action, enter one prompt, and submit. OpenHands starts one native
automation run with a linked conversation and visible result. Definitions and
runtime code live here; the App dispatches them through a signed local event.

There are twelve dedicated automations. Each role (SA, Frontend, Backend, QA) has
its own Propose, Update and Apply definition, named `OpenSpec <role> · <skill>`.
The seven legacy stage definitions and three generic role definitions are retired.

## Role actions

| Action | User input | Result and boundary |
| --- | --- | --- |
| OpenSpec <role> · Propose | Role, new change name, prompt; current requirement provides context | New planning artifacts and requirement record with all four roles; no implementation |
| OpenSpec <role> · Update | Role and revision prompt | Revise the current requirement's planning coherently; no implementation |
| OpenSpec <role> · Apply | Role and optional guidance prompt | Implement and verify only that role's tagged tasks; leave other roles unchanged |

Submitting Update explicitly approves artifact edits needed for the stated
revision. Submitting Apply authorizes implementation of that role's current
planned tasks. Unanswered material questions and changes outside that scope stop
the run. Completion never launches another action. Done on the board still
requires SA, Frontend, Backend, and QA to finish.

Examples: SA → Propose → `Plan task attachments with size limits and clear failure
states`; Frontend → Update → `Clarify keyboard focus after a failed save`;
Backend → Apply → `Follow the existing built-in HTTP conventions`; QA → Apply →
`Verify keyboard and failed-request scenarios`. Any of the four roles can submit
any of the three actions. Propose plans nonempty tasks for every role even when
its selected perspective is QA or Backend.

The fixed deployment configuration is `role-workflow.json`:

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
planning artifacts and `openspec/requirements.json`. Existing project-local
OpenSpec skills are read from `skill_root`; no replacement skills are installed.
The runner uses the pinned `npx --no-install openspec` CLI with an explicit
`--store openspec-store` for all change operations. A missing or mismatched store
registration blocks dispatch.

Install/connect the twelve dedicated role automations from the board's automation setup
action, then submit a role action from a requirement. A role automation's ordinary
zero-input **Run** is intentionally rejected because it lacks a role and request
context. Setup, refresh, and status checks never start an agent.

New role conversations carry native tags for `requirement` (for example,
`REQ-006`), `role` (`SA`, `Frontend`, `Backend`, or `QA`), `openspecstage` (such as
`apply`) and `openspecskill` (such as `openspec-apply-change`). These are set when
the conversation is created, alongside its existing change and automation run
tags. For Propose, `requirement` identifies the selected context requirement and
`openspecchange` identifies the new target change. Existing conversations retain
their original tags and remain available after definition retirement.

New conversation names use `[Role] <OpenSpec change name>`, for example
`[SA] add-task-quick-capture` or `[Backend] add-task-attachments`. Propose uses
the new target change; Update and Apply use the selected requirement's change.
The runner saves the title before starting the queued agent message and disables
automatic title generation. Existing conversation names remain unchanged.

Use one local OpenHands launcher for the shared automation database. Multiple
launchers on different ports can share the SQLite queue while keeping packages
in different storage directories; a competing dispatcher can then fail with a
missing tarball. Browser and desktop clients should connect to the same backend.

Successful Propose registers a stable new `REQ-NNN` ID, derived from the highest
existing ID while holding the store lock. Its title/summary come from the prompt,
owners start Unassigned, and every role starts in Backlog with unchecked tasks.
If planning is blocked, no record is registered; inspect any partial artifacts
before deciding how to recover. Update and Apply do not rewrite board metadata.

Role requests use source `openspec-role-dashboard`, schema
`openspec-role-dashboard/v1`, and event type `<stage>.requested`. The exact event
fields are `schema`, `type`, `stage`, `approval`, `request_id`, `spec_store`,
`requirement_id`, `context_change`, `role`, `change`, and `request`. Prompt text
cannot override configured workspace, store, skill root, profile, or timeout.
OpenHands delivers custom webhooks as an exact three-field wrapper:
`{"payload": <signed request>, "source_override": "openspec-role-dashboard",
"event_key": "<stage>.requested"}`. The runner validates this routing metadata
before unwrapping the request; raw request delivery remains supported. Unknown
wrapper fields, wrong sources, and mismatched event keys are rejected.
Propose and Update require a prompt of at most 10,000 characters; Apply may omit
guidance. The current requirement/change association must match store metadata.

The runner checks the envelope before mutable preflight, locks both store and
workspace, and consumes each request UUID at most once. It preserves saved
conversation confirmation/security settings and sends normal lifecycle callbacks.
After the agent finishes, it audits file scope and validates the change using
OpenSpec. Propose and Update must leave implementation files unchanged. Apply may
only change its role's task checkboxes in the store and must supply concrete
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
- Initial change: `add-task-completion`

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
pair IDs, preserves the signing source, and never starts a conversation.

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
