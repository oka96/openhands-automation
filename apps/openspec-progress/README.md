# OpenSpec progress

A local OpenHands App showing active OpenSpec changes, planning artifacts,
dependencies, and implementation task checklists. Select a change to inspect it;
use **Refresh** after an agent updates its files. The **Run Explore automation**
panel sends a prompt and parameters to the existing Explore automation. Page loads
and refreshes only read progress; starting Explore requires an explicit submission.

The initial project directory is `/Users/oka/Desktop/openHanda-demo`. Change it
using **Project directory → Load project**. The directory is on the connected
Agent Server machine, and must be the exact OpenSpec project root. The App saves
this directory and the last submitted request/run IDs in browser storage, separately
for each backend. Prompts, parameters, and credentials are not saved there.

## Requirements

- OpenHands Canvas with manifest schema 1 / host API 1 routed Apps.
- A local Agent Server with `/api/bash/execute_bash_command` support.
- Node.js and npm available to that server, plus the project's installed OpenSpec
  CLI. Tested with OpenSpec 1.14.0, Canvas 1.24.0, and Agent Server 1.49.6.
- For Explore: the native local Canvas launcher, Automation 1.15.1, Python 3.10+,
  and the updated Git-synced `OpenSpec 01 · Explore` definition.

The App runs a fixed, embedded collector through the host's authenticated Agent
Server adapter. It invokes `npx --no-install openspec list`, `status`, and
`instructions apply`, each with JSON output. It does not install packages or
start an agent. Project paths use structured `cwd`; change names are validated
and passed as data. No session key, model credential, or separate web service is
needed for progress collection. Cloud backends are not supported.

## Run Explore with inputs

1. Sync this repository's automation definitions in **Automate → Git Sync**.
2. Open **Run Explore automation** and choose **Connect Explore** once. This
   registers the signed local `openspec-dashboard` source; it starts no agent.
3. Enter a kebab-case change name and a requirement or question to investigate.
4. Optionally provide JSON parameters, for example
   `{"focus":"accessibility","max_options":3}`. Choose **Run Explore**.
5. Open the returned automation run to review its conversation and result.

The existing automation ID and history are preserved. Change, prompt, and
parameters belong to this run; the shared bundle is untouched. Workspace and
profile remain fixed by the automation. Explore investigates read-only and stops;
Propose, Apply, Sync, and Archive remain separate human decisions.

The native manual-dispatch endpoint has no input body. A fixed embedded Python
helper therefore submits a signed event through the native Automation API. It
uses service coordinates advertised by `/server_info`, and the launcher's
`OPENHANDS_AUTOMATION_API_KEY` environment variable entirely inside Agent Server.
The browser never receives credentials. No daemon, extra website, or public
webhook exposure is needed. Native history labels these as **event** runs.

The helper stores a generated source key, with private permissions, below the
Agent Server home at `.openhands/apps/openspec-progress/automation/`. It never
registers the reserved `openspec-manual` source. It requires an unambiguous Explore
definition and refuses dispatch if another enabled automation uses its source.
Up to 100 local automation/webhook definitions are supported.

Prompt size is limited to 10,000 characters and parameters to an 8 KiB JSON object.
The helper journals request IDs and the runner rejects replays. If a connection
fails after submission, inspect native history before selecting **Start another
request**: it does not automatically retry an uncertain run. Pending connection
setup also fails closed; inspect the source registration before reconnecting.

## Install

In OpenHands **Customize → Apps → Add app**, enter:

| Field | Value |
| --- | --- |
| App source | `github:oka96/openhands-automation` |
| Ref | A reviewed commit SHA, or `main` |
| Repository path | `apps/openspec-progress` |

For a local installation, use the App directory itself:
`/Users/oka/Desktop/openhands-automation/apps/openspec-progress`.

Installation leaves the App disabled. Review its source and revision, then choose
**Enable trusted app**. Apps execute JavaScript inside Canvas and can make
authenticated requests to the active Agent Server. Open **OpenSpec progress**
from the Apps navigation. Its route is `/extensions/openspec-progress/progress`;
change details use `/extensions/openspec-progress/progress/changes/<change>`.

Apps are installed separately from Automation Git Sync. Pushing this package
does not update an installed copy; reinstall the reviewed revision to update it.

## Develop and verify

From this directory:

```sh
npm ci
npm run check
```

The package has no runtime dependencies. esbuild and jsdom are development tools.
The build embeds scoped CSS and the collector into one browser ESM module,
validates `dist/extension.js`, then copies it to the checked-in `extension.js`.
Commit source, lockfile, manifest, and that entrypoint together.

Tests exercise the collector and the actual bundle's routing, cleanup, text-safe
rendering, malformed output, failed refreshes, partial task data, explicit dispatch,
Unicode inputs, duplicate submission, and uncertain outcomes. Python tests cover
signed events, private state, unchanged shared configuration, and routing guards.
Also run the
installed `canvas-extension-api/scripts/validate-extension.mjs` gate and check the
bundle in Chromium through a Blob URL. Before reporting native Canvas compatibility,
exercise root/nested routes, refresh, reload, and disable/re-enable in Canvas.

## Reading the dashboard

Planning status and task counts come from OpenSpec at refresh time. They are not
independent evidence that implementation, tests, review, or release checks passed.
Archived changes are outside this page's active-change inventory. Zero tasks is
shown as no tracked tasks, rather than 100% complete. If task tracking is unavailable,
planning artifacts remain visible with an explanation. A failed refresh labels any
retained snapshot as stale.

The collector limits each CLI command to 12 seconds and dashboard JSON to 128 KiB.
Oversized or incomplete results fail visibly instead of displaying truncated counts.
Updates are manual; there is no background polling or scheduled automation.
