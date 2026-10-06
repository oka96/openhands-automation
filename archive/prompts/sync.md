# Sync delta specs into main specs

The human manually selected Sync for the named change. This authorizes the
OpenSpec sync operation only. Read `.agents/skills/openspec-sync-specs/SKILL.md`.

Before writing main specs, check current task completion, inspect implementation
against the delta's scenarios, and run `npm run spec:validate`, `npm test`, and
`npm run test:acceptance`. Stop if tasks, tests, or implementation are incomplete,
or if there is any known unresolved finding. The human should run independent
Verify before this stage; do not describe these checks as an independent review.

Merge the named change's deltas using the skill's exact rules and the CLI's current
spec instructions. Preserve unrelated main-spec content. Do not modify application
code or move the active change. Validate the resulting specs, summarize the exact
requirements added/modified/removed, and leave archive as a separate human choice.
