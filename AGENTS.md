# OpenHands OpenSpec automations

This repository stores local OpenHands Automation Git Sync definitions. The target
application is configured in `workflow.json`; this repository is not that application.

- Edit `workflow.json`, `prompts/`, and `runtime/run.py`, then run `npm run build`.
- `automations/` contains complete generated bundles required by Git Sync. Commit them.
- Preserve the reserved `openspec-manual` trigger and constant-false filter for
  stages 02–07; never register that source. Explore also accepts explicit dashboard
  requests through the signed `openspec-dashboard` source. Validate its exact
  envelope, workspace, stage, and request ID; never advance to another stage.
- Never put credentials, session keys, or model tokens in files. Use the runtime's
  injected environment and the user's saved OpenHands agent profile.
- Keep the runtime Python standard-library only. Do not introduce ADLC skills:
  prompts must reuse the target's existing OpenSpec skills.
- Run `npm test` and `npm run check` before committing.
- Do not modify the target application while maintaining these definitions.
- Do not commit or push target-application work from an automation. Each stage
  stops at its stated boundary and reports blockers honestly.

Apps in `apps/` are independent packages, installed separately from Automation Git
Sync. Keep each App's source, manifest, build tooling, tests, and checked-in
`extension.js` inside its package. Run its `npm run check` as well as the root
checks. Progress collection is read-only. Only the explicit Explore action may
dispatch a run; ordinary page loads and refreshes must never start an agent.
