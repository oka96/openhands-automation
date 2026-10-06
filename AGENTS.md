# OpenHands OpenSpec automations

This repository stores local OpenHands Automation Git Sync definitions. The target
application is configured in `role-workflow.json`; this repository is not that application.

- Edit `role-workflow.json`, `prompts/`, and `runtime/`,
  then run `npm run build`. Generate exactly 12 fixed role/action bundles:
  SA, Frontend, Backend and QA each have Propose, Update and Apply, using the saved agent profile.
  Review, Commit and Merge Request definitions are retired; pause them and preserve their history.
- `automations/` contains complete generated bundles required by Git Sync. Commit them.
- The seven numbered stages and three generic role definitions are retired. Keep
  their recovery archive outside `automations/`; never regenerate or reconnect them.
- Role actions use the separate signed `openspec-role-dashboard` event source.
  Require a validated explicit event matching the bundle’s fixed role and stage,
  including prompt, selected
  requirement, canonical change/spec ID, and current context change. Events use schema v3. Native zero-input Run is unsupported.
  Keep deployment paths/profile fixed in `role-workflow.json`; event inputs must
  never override them. Validate store registration and current folder association,
  lock both store and workspace, and reject replayed request IDs.
- Requirement identity comes only from the role change directory:
  openspec/changes/<SA|FE|BE|QA>-<PREFIX>-<digits>-<feature>. Preserve exact prefix
  and digits. Never require or create requirements.json or another global index.
- Role Propose scaffolds one new role-owned change for the selected requirement.
  The role-specific sa/frontend/backend/qa schema stores proposal.md, design.md,
  specs/<capability>/spec.md and tasks.md in that independent folder. The runner
  creates the exact uppercase folder, immutable scope.json and role-bound .openspec.yaml because the pinned CLI's
  new-change command is lowercase-only; its existing-change commands accept it.
  Update edits that change's planning from the submitted
  revision prompt; that explicit submission authorizes those scoped artifact
  edits without an additional generic per-artifact confirmation, including repair
  of partial planning. Apply implements only the selected change's tasks and
  checks only tasks with concrete implementation evidence. Code validation and
  regression execution stay local unless the submitted prompt requests them.
  Leave unrun validation tasks unchecked; do not add validation UI or delivery
  gates. Untagged tasks inherit its role;
  explicit role tags must agree. Preserve stage boundaries, sibling changes,
  main specs and schema configuration. Optional Kanban Markdown context is display
  data; folder names and task evidence remain authoritative.
- Never put credentials, session keys, or model tokens in files. Use the runtime's
  injected environment and the user's saved OpenHands agent profile.
- Keep the runtime Python standard-library only. Do not introduce ADLC skills:
  prompts must reuse the target's existing OpenSpec skills.
- Run `npm test` and `npm run check` before committing.
- Do not modify the target application while maintaining these definitions.
- Automated turns stop after planning or implementation and must not commit or push.
  Review, commit and merge are user-directed follow-up actions in the related
  conversation. Never dispatch Git delivery from the Apps. SA remains spec-only.
  Each automated stage stops at its boundary and reports blockers honestly.

Apps in `apps/` are independent packages, installed separately from Automation Git
Sync. Keep each App's source, manifest, build tooling, tests, and checked-in
`extension.js` inside its package. Run its `npm run check` as well as the root
checks. Progress collection is read-only. Explicit Explore and submitted role
Propose/Update/Apply actions may dispatch native automation runs; ordinary page
loads, setup, status checks, and refreshes must never start an agent. The current
requirement board is maintained separately in `/Users/oka/Desktop/openhands-apps`.
