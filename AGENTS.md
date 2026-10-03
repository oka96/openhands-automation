# OpenHands OpenSpec automations

This repository stores local OpenHands Automation Git Sync definitions. The target
application is configured in `role-workflow.json`; this repository is not that application.

- Edit `role-workflow.json`, `prompts/`, and `runtime/run.py`,
  then run `npm run build`. Generate exactly twelve fixed role/skill bundles:
  SA, Frontend, Backend and QA each have Propose, Update and Apply.
- `automations/` contains complete generated bundles required by Git Sync. Commit them.
- The seven numbered stages and three generic role definitions are retired. Keep
  their recovery archive outside `automations/`; never regenerate or reconnect them.
- Role actions use the separate signed `openspec-role-dashboard` event source.
  Require a validated explicit event matching the bundle’s fixed role and stage,
  including prompt, selected
  requirement, canonical spec ID, and current context change. Events use schema v2. Native zero-input Run is unsupported.
  Keep deployment paths/profile fixed in `role-workflow.json`; event inputs must
  never override them. Validate store registry and current metadata association,
  lock both store and workspace, and reject replayed request IDs.
- Role Propose adds one role-owned spec to the selected requirement only after
  successful artifact validation. The role-specs schema stores specs/<ID>/spec.md
  and tasks/<ID>.md inside the existing requirement change. Shared proposal/design
  and sibling artifacts remain read-only. Update edits planning from the submitted
  revision prompt; that explicit submission authorizes those scoped artifact
  edits without an additional generic per-artifact confirmation. Apply implements
  only the selected spec's tasks and checks only tasks with verification evidence.
  Preserve stage boundaries, other roles, other changes, main specs, and metadata.
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
checks. Progress collection is read-only. Explicit Explore and submitted role
Propose/Update/Apply actions may dispatch native automation runs; ordinary page
loads, setup, status checks, and refreshes must never start an agent. The current
requirement board is maintained separately in `/Users/oka/Desktop/openhands-apps`.
