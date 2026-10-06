# Retired workflow reference

Historical documentation only. These definitions were retired on 2026-10-04. Do not use the old installation or sync instructions.

The original prompt templates are preserved in `archive/prompts/`.

# OpenSpec stages in OpenHands

Run **Propose**, **Update**, or **Apply** for SA, Frontend, Backend, or QA from the
requirement board in `/Users/oka/Desktop/openhands-apps`. Select a requirement,
role, and action, enter one prompt, and submit. OpenHands starts one native
automation run with a linked conversation and visible result. Definitions and
runtime code live here; the App dispatches them through a signed local event.

The seven original OpenSpec stages remain available through **Automate** and Git
Sync. The original progress App's Explore action also remains supported.

## Role actions

| Action | User input | Result and boundary |
| --- | --- | --- |
| OpenSpec Role · Propose | Role, new change name, prompt; current requirement provides context | New planning artifacts and requirement record with all four roles; no implementation |
| OpenSpec Role · Update | Role and revision prompt | Revise the current requirement's planning coherently; no implementation |
| OpenSpec Role · Apply | Role and optional guidance prompt | Implement and verify only that role's tagged tasks; leave other roles unchanged |

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

Install/connect the three role automations from the board's automation setup
action, then submit a role action from a requirement. A role automation's ordinary
zero-input **Run** is intentionally rejected because it lacks a role and request
context. Setup, refresh, and status checks never start an agent.

New role conversations carry native tags for `requirement` (for example,
`REQ-006`), `role` (`SA`, `Frontend`, `Backend`, or `QA`), `openspecstage` (such as
`apply`) and `openspecskill` (such as `openspec-apply-change`). These are set when
the conversation is created, alongside its existing change and automation run
tags. For Propose, `requirement` identifies the selected context requirement and
`openspecchange` identifies the new target change. Legacy stage runs include their
mapped skill without inventing a role or requirement. Existing conversations
retain their original tags.

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

The three role bundles live in `automations/openspec-role-propose`,
`automations/openspec-role-update`, and `automations/openspec-role-apply`. Each
contains the same standalone runtime plus its stage prompt and fixed config.

These definitions target the existing local demo:

- Workspace: `/Users/oka/Desktop/openhands-demo`
- OpenHands Canvas: `http://127.0.0.1:8000`
- Saved agent profile: `codex-acp-demo`
- Initial change: `add-task-completion`

The automation runner uses OpenHands Agent Server to start a conversation with
that saved profile. With the current profile, Codex ACP performs the agent work;
OpenHands manages dispatch, conversations, logs, and run status.

## Original seven-stage workflow

For a view of active changes, artifacts, and task checklists, install
the [OpenSpec progress App](apps/openspec-progress/README.md). It runs inside
OpenHands and refreshes from the target project's OpenSpec CLI. Its explicit
**Run Explore automation** panel submits requirements to the existing Explore
automation without changing its shared configuration. Apps have a
separate installation flow from Automation Git Sync.

```text
Explore → Propose → human reviews artifacts → Apply → Verify
              ↑                                │       │
              └──────── Update ← findings ──────┴───────┘

Successful verification → human selects Sync → human selects Archive
```

Each arrow is a human decision, not an automatic transition. A stage can perform
many steps internally, but its completion never dispatches another stage.

| Automation | Work performed | Boundary |
| --- | --- | --- |
| OpenSpec 01 · Explore | Investigate the request or current change | Read-only |
| OpenSpec 02 · Propose | Generate proposal, scenarios, design, and tasks | Stop for review; no application edits |
| OpenSpec 03 · Update | Revise existing planning artifacts from a request | Stop for review; no application edits |
| OpenSpec 04 · Apply | Implement approved tasks and run required checks | Leave specs unsynced and change active |
| OpenSpec 05 · Verify | Fresh conversation reviews code, tests, and browser scenarios | Report findings; no fixes |
| OpenSpec 06 · Sync specs | Merge delta specs into main specs | Keep change active |
| OpenSpec 07 · Archive | Archive completed, already synced work | Block on incomplete tasks, unsynced deltas, or failed checks |

OpenHands requires a cron or event trigger, and Canvas 1.24.0 disables **Run** for
inactive definitions. Stages 02–07 therefore stay active with the reserved
event source `openspec-manual` and event `manual-only`. That source is deliberately
not registered, there is no schedule, and a constant-false JMESPath filter rejects
all automatic event matches. The runner also validates this trigger configuration
and rejects delivered event payloads, so only ordinary manual dispatch can start an
agent. Do not register
a webhook for this source or replace its trigger with a schedule. Git Sync's
refresh interval never authorizes the next OpenSpec stage.

Explore uses the signed local `openspec-dashboard` event source and accepts only
the `explore.requested` envelope. Each App submission creates one native run with
its own change name, prompt, and parameters. The service labels these runs as event
triggered; there is no schedule or automatic transition. The runner validates the
stage and fixed workspace, and refuses replayed request IDs. Ordinary **Run** on
the Explore automation still uses the bundled defaults.

Selecting Apply is the human's approval of the configured change's current
planning artifacts. Selecting Sync or Archive is a separate explicit approval of
that operation. These are workflow boundaries, not operating-system write
restrictions or a durable dependency engine. Read Verify's result before moving
on; a checked task box alone does not establish correctness.

## Choose the request

For Explore, open the progress App, expand **Run Explore automation**, and connect
it once after syncing these definitions. Enter a change name, prompt, and optional
JSON object, then select **Run Explore**. Follow its run link for the conversation
and result. Parameters are investigation context, not overrides for the workspace,
profile, or stage. Later stages still require their own explicit approval.

For shared defaults and stages 02–07, edit `workflow.json` before running work on a
different change:

```json
{
  "workspace": "/Users/oka/Desktop/openhands-demo",
  "change": "your-new-change",
  "request": "Describe the behavior, scope, and acceptance criteria here.",
  "profile": "codex-acp-demo",
  "timeout_seconds": 1800,
  "canvas_url": "http://127.0.0.1:8000"
}
```

Then rebuild, test, commit, push, and press **Sync now** in OpenHands:

```sh
cd /Users/oka/Desktop/openhands-automation
npm run build
npm test
npm run check
git add workflow.json prompts runtime automations
git commit -m "Configure OpenSpec change"
git push origin main
```

Open the intended stage, confirm its configured change, and select **Run**.
The ordinary Run endpoint in this OpenHands version does not accept a custom
input payload or display a request form; those ordinary runs use the bundled
configuration from the most recent successful Git Sync. The App's parameterized
Explore action uses the supported signed-event API instead of this endpoint.

For a new change, set a new kebab-case name and a concrete request, then start at
Explore or Propose. To revise an existing change, supply the revision request and
run Update. The checked-in request is intentionally empty: Propose and Update
fail clearly until you describe the work. Propose also refuses to overwrite an
existing change. Explore can inspect the initial demo change immediately.

## Connect Git Sync

In the local OpenHands instance, open **Automate → Git Sync**:

| Setting | Value |
| --- | --- |
| Repository URL | `https://github.com/oka96/openhands-automation.git` |
| Branch | `main` |
| Path | `automations` |
| Sync every | `0` for manual sync |

Save and sync, then verify that all ten named automations appear (seven original
stages and three role actions). An overall
successful sync can still skip an invalid directory, so check the imported rows.
For periodic configuration refresh, set a positive sync interval in that page;
preserve the individual automations' generated triggers and runner guards.

Git Sync is bidirectional: it pulls, imports, exports service-side edits, and
pushes. It needs write access if OpenHands has changes to export. Use existing Git
authentication or configure a suitable token in OpenHands settings; never add a
token to this repository. Unsynced service-side edits win conflicts for a cycle,
so avoid editing the same definition in the UI and Git simultaneously. Sync and
pull before making subsequent Git edits. Removing a synced automation directory
can remove its corresponding automation from OpenHands.

## How the bundles work

```text
workflow.json + prompts/common.md + prompts/<stage>.md + runtime/run.py
                              │ npm run build
                              ▼
automations/openspec-01-explore/
  automation.yaml
  tarball/
    config.json
    prompt.md
    run.py
```

Every stage has a self-contained bundle because Git Sync uploads each `tarball/`
independently. The `.yaml` metadata uses JSON syntax, a valid YAML subset, so the
builder needs no YAML dependency. Edit the source files and regenerate rather
than editing the generated copies. OpenHands may normalize the YAML when it
exports an edited definition; rebuilding restores the generated format.

The runner uses only Python's standard library. It gets the Agent Server URL and
session key from OpenHands' injected runtime environment, resolves the saved
profile by name, selects the explicit local workspace, and links its conversation
to the run. It preserves configured conversation confirmation settings. It holds
a per-workspace lock to prevent these automations from running concurrently,
pauses its conversation on timeout or errors, and sends the completion callback.
The service timeout includes cleanup time; role actions additionally reserve time
for their bounded postflight CLI checks.

A stage must return a final JSON result with `completed`, `blocked`, or `findings`.
Only `completed` with no findings produces a successful run. OpenHands shows a
failed run when human input, missing evidence, or a defect blocks progress; inspect
the linked conversation for the actionable explanation. If the conversation itself
needs tool approval, this version reports it as blocked rather than granting that
approval automatically.

This is designed for the current **native local** Agent Server, Canvas 1.24.0,
Automation 1.15.1,
and Agent Server 1.49.6. Docker or cloud deployments require accessible workspace
mounts and a different server-address policy; merely copying this Mac path into a
cloud automation will not work. Existing user work is preserved, and the prompts
do not authorize committing or pushing the application repository.

## Validate locally

Python 3.10+ and npm are sufficient for this repository's checks; there are no npm
dependencies. The target demo needs its already installed Node.js/OpenSpec tools.

```sh
npm run build
npm test
npm run check
python3 automations/openspec-01-explore/tarball/run.py --check
python3 automations/openspec-role-propose/tarball/run.py --check
python3 automations/openspec-role-update/tarball/run.py --check
python3 automations/openspec-role-apply/tarball/run.py --check
```

`--check` validates local stage prerequisites without connecting to Agent Server
or running an agent. Unit tests use a fake API for lifecycle and failure cases.
Tests exercise all twelve role/action combinations with native custom-webhook
wrappers and normalized triggers, raw-event compatibility, invalid routing and
inputs, store/context mismatches, replay across both delivery forms, both locks, role scope,
new requirement registration, and completion evidence with temporary stores and
a fake agent. Native installation and live agent execution are separate checks;
passing a fake-agent test does not claim a model completed product work. Do not
run Apply, Sync, or Archive merely to test automation plumbing.

Validated on 2026-10-03: all 30 unit tests and bundle checks passed; Git Sync
imported all seven stages; a manual Explore run completed through `codex-acp-demo`
and reported its callback and linked conversation without system errors. The
demo's file fingerprint was identical before and after the run. Canvas labels
the completed custom task **Needs review**; open its conversation to review the
result and choose the next stage. This smoke test does not certify the other six
stages against a real change or replace an independent Verify run.

Local smoke-test run: `ae89264e-60bf-4e3e-a929-23d4d0b9510a`;
conversation: `eb824925-b0df-4ec2-8847-45be0ee123e3`.

Sources: [OpenHands Git Sync](https://docs.openhands.dev/openhands/usage/agent-canvas/git-sync),
[1.15.1 serializer](https://github.com/OpenHands/automation/blob/1.15.1/openhands/automation/git_sync/serializer.py),
[dispatch and callbacks](https://github.com/OpenHands/automation/blob/1.15.1/openhands/automation/router.py),
[Agent Server profile selection](https://github.com/OpenHands/software-agent-sdk/blob/v1.49.6/openhands-agent-server/openhands/agent_server/conversation_service.py).
