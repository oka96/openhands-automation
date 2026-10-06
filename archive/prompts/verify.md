# Independently verify the current implementation

Perform a fresh read-only review of the named change. Read AGENTS.md, current
specs, all change artifacts, relevant source and tests, and staged/unstaged diffs.
Include relevant nonignored untracked files. Do not read `.local/`. Do not edit
application files, specs, checkboxes, or planning artifacts. Do not run the ADLC
controller or delegate implementation; this conversation is the independent review.

Use the pinned CLI to inspect change status and apply instructions. Incomplete
implementation tasks block verification. Run `npm run spec:validate`, `npm test`,
and `npm run test:acceptance`. Inspect the API contract and edge cases, then check
each applicable browser scenario using an already available approved browser tool.
Checked task boxes and an earlier agent's summary are not browser evidence.
Test failures, unavailable tooling, or missing evidence must not produce success.

Report concrete defects as `findings` with file paths and actionable explanations.
Report incomplete checks as `blocked`. Use `completed` only when all required
checks passed and there are no unresolved findings. State the tested change and
current git revision plus local diff state so the human can recognize stale evidence.
Recommend Update/Apply for corrections or Sync after a successful human review.
