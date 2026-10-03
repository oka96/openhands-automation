# Explore

Read `.agents/skills/openspec-explore/SKILL.md` and use its investigation workflow.
This automation is read-only: do not create or edit application code, specs,
planning artifacts, task checkboxes, or repository settings.

Run `npx --no-install openspec list --json`, inspect current specs, and inspect
the named change if it exists. If a request is supplied, investigate that topic;
otherwise report the named change's current state and next required decision.
Keep investigation proportional to the question. Distinguish existing behavior,
observed defects, assumptions, and possible future changes. Do not implement fixes.
Report evidence and concrete choices for the human before proposal or update.
