# Archive a completed, already synced change

The human explicitly selected Archive for the configured change. Read
`.agents/skills/openspec-archive-change/SKILL.md` and check current artifact status,
CLI-tracked task completion, validation, and delta-to-main-spec consistency.

This request selects "Archive now" ONLY when every task and artifact is complete,
required verification has succeeded, and every delta is already synced. It does
not select "Sync now", "Sync anyway", or "Archive without syncing", and does not
approve archiving incomplete work. If any of those choices is needed, return
`blocked` and name the required action. Do not silently answer a confirmation.

Run `npm run spec:validate`, `npm test`, and `npm run test:acceptance` before moving
the change. Stop on any failure or known unresolved finding. Check browser evidence
as required by the change; if it cannot be established, block archive.

Only after these checks pass, archive using the skill's date/path conventions.
Do not edit application code or main specs during this stage. Report the archive
location and verification evidence. Do not commit or push.
