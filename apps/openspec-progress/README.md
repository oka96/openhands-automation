# OpenSpec progress

A read-only OpenHands App showing active OpenSpec changes, planning artifacts,
dependencies, and implementation task checklists. Select a change to inspect it;
use **Refresh** after an agent updates its files. The page never launches a stage,
checks a task, edits a specification, or archives a change.

The initial project directory is `/Users/oka/Desktop/openHanda-demo`. Change it
using **Project directory → Load project**. The directory is on the connected
Agent Server machine, and must be the exact OpenSpec project root. The App saves
only this directory in browser storage, separately for each backend.

## Requirements

- OpenHands Canvas with manifest schema 1 / host API 1 routed Apps.
- A local Agent Server with `/api/bash/execute_bash_command` support.
- Node.js and npm available to that server, plus the project's installed OpenSpec
  CLI. Tested with OpenSpec 1.14.0, Canvas 1.24.0, and Agent Server 1.49.6.

The App runs a fixed, embedded collector through the host's authenticated Agent
Server adapter. It invokes `npx --no-install openspec list`, `status`, and
`instructions apply`, each with JSON output. It does not install packages or
start an agent. Project paths use structured `cwd`; change names are validated
and passed as data. No session key, model credential, or separate web service is
needed. Cloud backends are not supported by this first version.

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
rendering, malformed output, failed refreshes, and partial task data. Also run the
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
