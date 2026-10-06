# OpenSpec role automation

This repository owns the OpenSpec workflow used by OpenHands Kanban and the SA,
Frontend, Backend and QA role Apps in `/Users/oka/Desktop/openhands-apps`.
Each role has three native automations, for **12 active definitions** in total.

| Action | Input | Result |
| --- | --- | --- |
| Propose | Requirement, feature name, prompt; application bindings for a new SA requirement | Create one independent role spec with unchecked tasks |
| Update | Existing role spec and revision prompt | Update its planning and save a before/after diff |
| Apply | Existing role spec and optional implementation prompt | Implement its tasks in the bound workspace; SA prepares its design handoff |

The workflow focuses on implementation. Code validation, acceptance checks and
regression execution stay local. Apply runs them only when explicitly requested
in the submitted prompt. QA implements regression code in its own repository.
Unrun checks are never reported as passed and validation-only tasks stay unchecked.
Review, commit and merge are manual actions in the related conversation.
Automation enforces request identity and role scope, and stops at implementation.

## Using a role workflow

Open a role from OpenSpec Kanban. Select a requirement and a Role spec, choose a
node, complete its form and press **Run**. Selecting a node, loading a page,
reading history or refreshing status never starts an agent. Every submission
starts one native automation; completion never advances to the next node.

SA can create a new requirement from its home page. Enter a canonical requirement
ID such as `BOOK-002`, a feature name such as `room-booking`, a prompt and the
impacted applications (ID, display name, role and HTTPS GitHub repository URL).
SA may cover several repositories. It creates the shared contract and hands code
implementation to the downstream roles. Frontend and Backend specs reference SA
and each bind one repository. QA references SA, Frontend and Backend and binds
one regression repository. Downstream Propose selects an application from SA.
All later actions preserve the selected spec's `scope.json` and role schema.

Examples: SA Propose `Plan a booking system with room capacity and no overlaps`;
Backend Update `Add cancellation to the API contract`; Frontend Apply `Implement
the booking form using the current component conventions`; QA Apply `Implement
regression coverage for overlap and cancellation, leaving execution local`.
The same definitions accept different requirements and prompts.

Use **Open conversation** for the selected role spec to inspect changes and handle
commit or merge when needed. The button resolves the newest related conversation
from native history, including a running conversation once created. It preserves
the selected backend and starts no work. Without a conversation, run Propose,
Update or Apply and refresh. The App opens the conversation; choose its Commits
panel inside OpenHands. No public App API selects that panel automatically.

## Ownership and workspaces

- `runtime/actions.json`: the shared action catalog, copied into bundles and App presentation metadata.
- `runtime/control.py`: connection, signing, dispatch, native status, scoped conversation lookup and evidence reads.
- `runtime/collector.cjs`: authoritative read-only Kanban aggregation and scope checks.
- `runtime/run.py`: event validation, locks, workspace preparation, model conversations and role audits.
- `runtime/delivery.py`: spec revisions, conversation associations and read-only historical delivery records.
- `prompts/`: short action exceptions and one shared execution/result contract; the OpenSpec skills own the workflow steps.

Apps are visual clients. They contain fixed transport loaders that call the local
Automation runtime and display its returned data. This repository must therefore
be available to the Agent Server at `/Users/oka/Desktop/openhands-automation`.
No workflow business logic is duplicated in the Apps.

### Prompt structure

Each generated `prompt.md` starts with a skill reference:

```md
Use [$openspec-apply-change](<${skill_path}>) for `${change}`.
Read that SKILL.md and follow it within the run boundaries below.
```

The runner replaces four template fields once: `skill_path`, `change`, `context`
and `request`. The skill path comes from the configured skill root and action
catalog. Context contains only role/action, selected spec and requirement,
store, prepared workspace and related changes. The request is a JSON string;
its literal placeholders, quotes and shell syntax are never evaluated.

This is a textual instruction to read the skill, not a shell command or a
guaranteed slash-command invocation. The skill lives outside the conversation's
checkout, so its explicit path matters. Tasks and repository bindings are read
from the selected spec instead of duplicating them in the prompt.

Only automation-specific exceptions remain: Propose uses the runner-created
folder, Update is already authorized to revise/repair planning, and Apply keeps
validation local and reports evidence. A short shared section preserves role
boundaries and the terminal JSON required by the runner. Event validation,
workspace preparation, locking and postflight audits remain in Python.
Retired stage templates are kept under `archive/prompts/`; they are not built.

`role-workflow.json` fixes the store, managed workspace parent, skill root, saved
profile and timeout. Requests cannot override them. The current deployment uses:

- Store: `/Users/oka/Desktop/openspec-store`, registered as `openspec-store`
- Workspace parent: `/Users/oka/Desktop/openhands-automation/workspaces`
- Existing skills: `/Users/oka/Desktop/openhands-demo/.agents/skills`
- Saved profile: `codex-acp-demo`
- OpenHands: `http://127.0.0.1:8000`

Before a downstream role conversation, the runner creates
`<workspace>/<spec-id>/<application-id>`, clones its bound repository and checks
the Git root and origin. Subsequent actions reuse the checkout without pulling or
resetting user changes. The conversation runs in that checkout. SA actions run
directly in the registered spec store, so the conversation's files and Git panels
identify that repository. SA never clones or changes code. Existing conversations
keep their original workspace; the corrected SA workspace applies to new runs.
The pinned OpenSpec CLI runs from the registered store, with explicit
`--store`, so code repositories need no OpenSpec installation.

Scope audits reject edits to siblings, schema bindings and other managed
checkouts. These controls are not an OS sandbox. Missing upstreams, clone failures
or mismatched origins prevent conversation startup. Credentials stay in the
runtime environment and saved profile, never tracked files or event inputs.

## Revisions and delivery receipts

Every modifying model run saves the selected spec's before/after diff, including
partial changes from failed runs. History is scoped by store, role, requirement
and spec. Private JSON records are stored under
`~/.openhands/role-delivery/<store-hash>/<spec-id>/{revisions,reviews,deliveries}`.
The App lists the latest 50 records per kind and fetches a diff only when selected.
Spec snapshots are bounded to 200 files and 2 MiB of input content; linked paths
are rejected. Binary and mode changes are displayed. Old review and delivery
receipts remain readable as history, without actions to rerun retired stages.

Conversation associations are saved before agent execution under
`~/.openhands/apps/openspec-progress/role-conversations/<run-id>.json`. The read-only
lookup verifies exact store, requirement, role and spec identity against native
runs, and uses validated terminal reports for older runs. It examines at most
1000 runs per active action and reports unavailable history explicitly. A deleted
conversation is not recreated; OpenHands handles its missing-conversation page.

## Events and native results

Requests use signed source `openspec-role-dashboard`, schema
`openspec-role-dashboard/v3` and event `<stage>.requested`. Required fields are
`schema`, `type`, `stage`, `approval`, `request_id`, `spec_store`, `requirement_id`,
`context_change`, `role`, `spec_id`, `change`, and `request`. Optional structured
fields are `application_id` for downstream Propose, `applications` for new SA
requirements. Removed delivery fields and stages are rejected.
New SA intake has empty `context_change`; existing-spec actions must select their
own folder. Propose/Update require a prompt of at most 10,000 characters.

The runtime checks native routing metadata and fixed role/stage, locks the store
and workspace, and consumes each request UUID once. Native zero-input Run is
unsupported. Canonical folders are
`openspec/changes/<SA|FE|BE|QA>-<PREFIX>-<digits>-<feature>`; no requirements registry
is created. Preserve exact prefix/digits and the role's schema. Limits are 50
requirements, 20 specs per requirement and 500 tasks per requirement.

Native runs remain the execution history. Bounded, redacted outcomes live under
`~/.openhands/apps/openspec-progress/role-results/<run-id>.json`. The App shows
completion, dependency/input blockers, review needs or execution errors without
rewriting native history. Agent edits and partial failures remain available for
inspection. Newly checked tasks need concrete implementation evidence; reopening
an unsupported checked task needs an exact `task_corrections` reason. Pending
validation tasks are not silently marked complete. Requirement Done remains based
on all four roles' actual task files.

Model conversations use the spec ID as title and six tags: `requirement`, `role`,
`openspecstage`, `openspecspec`, `automationrunid`, `automationtrigger`. Automated
turns never commit or push; subsequent user instructions can request manual Git
actions within the conversation’s role scope.

## Build and connect

```sh
npm run build
npm test
npm run check
```

The generator emits all 12 complete bundles under `automations/`. Commit generated
files alongside sources. **Connect shared automations** installs or updates the
same role/action IDs and preserves their histories; it adds missing actions and
starts no agent. Reconnect after changing configuration or rebuilding bundles.
Use one local OpenHands launcher so dispatchers do not share a queue with different
tarball storage directories.

Connect pauses the twelve old Review, Commit and Merge Request definitions after
checking for pending/running work. It keeps their IDs, runs and conversations,
prunes their private connection bindings, and preserves the twelve active IDs.
Repeated connection is idempotent.

The earlier migration removes the seven recognized numbered stages and three generic
`OpenSpec Role` definitions, after checking for active runs. Their recovery archive
is `archive/2026-10-04-superseded-automations.tar.gz`; do not restore it under
`automations/`. Unrelated automations and all historical runs remain untouched.
Git Sync uses the `automations/` directory. Sync only the intended branch after
publishing its changes; an older revision can restore obsolete definitions.
