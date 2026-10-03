# OpenSpec stages in OpenHands

Run each OpenSpec process from the OpenHands **Automate** page. Git Sync imports
the definitions in this repository; a human selects **Run** for each stage.
No separate website, new ADLC skill, or Codex desktop automation is required.

These definitions target the existing local demo:

- Workspace: `/Users/oka/Desktop/openHanda-demo`
- OpenHands Canvas: `http://127.0.0.1:8002`
- Saved agent profile: `codex-acp-demo`
- Initial change: `add-task-completion`

The automation runner uses OpenHands Agent Server to start a conversation with
that saved profile. With the current profile, Codex ACP performs the agent work;
OpenHands manages dispatch, conversations, logs, and run status.

## Workflow and approval gates

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
inactive definitions. These definitions therefore stay active with the reserved
event source `openspec-manual` and event `manual-only`. That source is deliberately
not registered, there is no schedule, and a constant-false JMESPath filter rejects
all automatic event matches. The runner also validates this trigger configuration
and rejects delivered event payloads, so only ordinary manual dispatch can start an
agent. Do not register
a webhook for this source or replace its trigger with a schedule. Git Sync's
refresh interval never authorizes the next OpenSpec stage.

Selecting Apply is the human's approval of the configured change's current
planning artifacts. Selecting Sync or Archive is a separate explicit approval of
that operation. These are workflow boundaries, not operating-system write
restrictions or a durable dependency engine. Read Verify's result before moving
on; a checked task box alone does not establish correctness.

## Choose the request

Edit `workflow.json` before running work on a different change:

```json
{
  "workspace": "/Users/oka/Desktop/openHanda-demo",
  "change": "your-new-change",
  "request": "Describe the behavior, scope, and acceptance criteria here.",
  "profile": "codex-acp-demo",
  "timeout_seconds": 1800,
  "canvas_url": "http://127.0.0.1:8002"
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
input payload or display a request form; every run uses the bundled configuration
from the most recent successful Git Sync.

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

Save and sync, then verify that all seven named automations appear. An overall
successful sync can still skip an invalid directory, so check the imported rows.
For periodic configuration refresh, set a positive sync interval in that page;
preserve the individual automations' reserved event triggers and manual-run guards.

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
The 1800-second service timeout includes 30 seconds reserved for cleanup.

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
```

`--check` validates local stage prerequisites without connecting to Agent Server
or running an agent. Unit tests use a fake API for lifecycle and failure cases.
Live verification is a separate **Run** of Explore in OpenHands. Do not run Apply,
Sync, or Archive just to test the automation plumbing.

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
