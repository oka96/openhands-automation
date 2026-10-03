# Propose

Read `.agents/skills/openspec-propose/SKILL.md`. Create planning artifacts for the
configured new change from the supplied request. If the change already exists,
stop and recommend Update; do not overwrite it or invent a new name.

Inspect relevant implementation read-only before drafting. Produce the schema's
proposal, delta specs and scenarios, design, and tasks using the pinned CLI's
instructions. Run strict validation for the change. Record any assumptions.

This stage authorizes planning only. Do not implement even if the request says
"build" or "fix". Summarize the artifacts and remaining questions, and stop for
human review. The human must explicitly run Apply after approving these artifacts.
