# OpenHands OpenSpec automations

This repository stores local OpenHands Automation Git Sync definitions. The target
application is configured in `workflow.json`; this repository is not that application.

- Edit `workflow.json`, `prompts/`, and `runtime/run.py`, then run `npm run build`.
- `automations/` contains complete generated bundles required by Git Sync. Commit them.
- Preserve the reserved `openspec-manual` event trigger, its constant-false filter,
  and the runner's rejection of delivered events. Manual Run is the approval gate;
  do not register that source.
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
checks. The OpenSpec progress App is read-only; preserve that boundary.
