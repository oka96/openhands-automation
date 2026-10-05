# OpenSpec role automation

This repository owns the OpenSpec workflow used by OpenHands Kanban and the SA,
Frontend, Backend and QA role Apps in `/Users/oka/Desktop/openhands-apps`.
Each role has six native automations, for **24 definitions** in total.

| Action | Input | Result |
| --- | --- | --- |
| Propose | Requirement, feature name, prompt; application bindings for a new SA requirement | Create one independent role spec with unchecked tasks |
| Update | Existing role spec and revision prompt | Update its planning and save a before/after diff |
| Apply | Existing role spec and optional implementation prompt | Implement its tasks in the bound workspace; SA prepares its design handoff |
| Review | Existing role spec and target (`specs` or `code`) | Save the current diff as an immutable snapshot |
| Commit | Reviewed snapshot and commit message | Commit exactly those changes locally, without pushing |
| Merge Request | Reviewed snapshot and PR title | Create a unique branch, commit, push and open a GitHub pull request |

The workflow focuses on implementation. Code validation, acceptance checks and
regression execution stay local. Apply runs them only when explicitly requested
in the submitted prompt. QA implements regression code in its own repository.
Unrun checks are never reported as passed and validation-only tasks stay unchecked.
Review captures a diff; it is not a code-quality verdict. Delivery does not require
a test-result record. Request, repository scope and snapshot integrity checks
remain enforced by Automation.

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

Review the **Selected specifications** or **Bound code repository** target. SA
only offers specifications. Inspect **Reviewed changes**, then choose Commit or
Merge Request and explicitly select that snapshot. A changed file, mode, branch,
HEAD or origin requires another Review. Propose, Update and Apply never commit or
push from a model conversation. Delivery is deterministic and starts no model.

## Ownership and workspaces

- `runtime/actions.json`: the shared action catalog, copied into bundles and App presentation metadata.
- `runtime/control.py`: connection, signing, dispatch, native status and evidence reads.
- `runtime/collector.cjs`: authoritative read-only Kanban aggregation and scope checks.
- `runtime/run.py`: event validation, locks, workspace preparation, model conversations and role audits.
- `runtime/delivery.py`: revision records, Git snapshots and deterministic delivery.
- `prompts/`: bounded instructions for the three model actions and deterministic action descriptions.

Apps are visual clients. They contain fixed transport loaders that call the local
Automation runtime and display its returned data. This repository must therefore
be available to the Agent Server at `/Users/oka/Desktop/openhands-automation`.
No workflow business logic is duplicated in the Apps.

`role-workflow.json` fixes the store, managed workspace parent, skill root, saved
profile and timeout. Requests cannot override them. The current deployment uses:

- Store: `/Users/oka/Desktop/openspec-store`, registered as `openspec-store`
- Workspace parent: `/Users/oka/Desktop/openhands-automation/workspaces`
- Existing skills: `/Users/oka/Desktop/openhands-demo/.agents/skills`
- Saved profile: `codex-acp-demo`
- OpenHands: `http://127.0.0.1:8000`

Before a code conversation or code review, the runner creates
`<workspace>/<spec-id>/<application-id>`, clones its bound repository and checks
the Git root and origin. Subsequent actions reuse the checkout without pulling or
resetting user changes. The conversation runs in that checkout. SA and spec-only
deterministic actions use `<workspace>/<spec-id>/planning`; SA never clones or
changes code. The pinned OpenSpec CLI runs from the registered store, with explicit
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
Snapshots are bounded to 200 files and 2 MiB of input content; linked paths and
submodules cannot be delivered. Binary and mode changes are explicitly displayed.
A diff includes specification/task changes, not a test execution result.

Commit uses an isolated index and a verified immutable Git tree. It advances HEAD
only if the expected old commit still matches, then resets only the committed
paths in the real index. Unrelated staging remains intact. Repository commit hooks
are not executed; local validation is a separate activity. A normal configured
Git author identity is required.

Merge Request creates `codex/<spec-id>-<review-id-prefix>`, leaves that branch
checked out, and pushes the exact commit to the reviewed GitHub URL without force.
It uses the installed `gh` authentication to open a pull request against the branch
captured by Review. The supplied repositories use GitHub, where an MR is a pull
request. No automatic merge or deployment follows.

Receipts record `committing`, `committed`, `pushed` and `complete`, with the actual
commit, branch and PR URL. After a push/PR failure, retry the same snapshot, action
and message: automation resumes publication and searches for an existing PR to
avoid duplicates. A completed retry returns its existing receipt. If the commit
outcome is uncertain or the branch/HEAD moved after partial delivery, inspect Git
and the receipt before retrying; the runtime does not guess or force-reset work.

## Events and native results

Requests use signed source `openspec-role-dashboard`, schema
`openspec-role-dashboard/v3` and event `<stage>.requested`. Required fields are
`schema`, `type`, `stage`, `approval`, `request_id`, `spec_store`, `requirement_id`,
`context_change`, `role`, `spec_id`, `change`, and `request`. Optional structured
fields are `application_id` for downstream Propose, `applications` for new SA
requirements, `target` for Review/delivery, and `review_id`/`message` for delivery.
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
`openspecstage`, `openspecspec`, `automationrunid`, `automationtrigger`. Review and
Git delivery are native runs without model conversations.

## Build and connect

```sh
npm run build
npm test
npm run check
```

The generator emits all 24 complete bundles under `automations/`. Commit generated
files alongside sources. **Connect shared automations** installs or updates the
same role/action IDs and preserves their histories; it adds missing actions and
starts no agent. Reconnect after changing configuration or rebuilding bundles.
Use one local OpenHands launcher so dispatchers do not share a queue with different
tarball storage directories.

Connect retires only the seven recognized numbered stages and three generic
`OpenSpec Role` definitions, after checking for active runs. Their recovery archive
is `archive/2026-10-04-superseded-automations.tar.gz`; do not restore it under
`automations/`. Unrelated automations and all historical runs remain untouched.
Git Sync uses the `automations/` directory. Sync only the intended branch after
publishing its changes; an older revision can restore obsolete definitions.
