"""Role/spec dispatch contracts with real temporary stores and a fake agent/CLI."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest import mock
import uuid

SPEC = importlib.util.spec_from_file_location("role_runner", Path(__file__).parents[1] / "runtime/run.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
SUCCESS = {"status": "completed", "summary": "Verified the selected spec", "findings": [], "task_evidence": []}


class RoleRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.workspace, self.store = self.root / "workspace", self.root / "store"
        (self.workspace / "openspec").mkdir(parents=True)
        (self.workspace / "app.js").write_text("original implementation\n")
        for skill in set(runner.STAGES.values()):
            directory = self.workspace / ".agents/skills" / skill
            directory.mkdir(parents=True)
            (directory / "SKILL.md").write_text("Use the selected OpenSpec skill.")
        for role in runner.ROLES:
            for feature in ("first", "second"):
                self.create_spec(self.spec_id(role, feature), role)
        self.metadata_path = self.store / "openspec/requirements.json"
        (self.store / "openspec/config.yaml").write_text("schema: spec-driven\n")
        self.config = {"mode": "role", "stage": "apply", "workspace": str(self.workspace), "spec_store": str(self.store),
                       "store_id": "fixture-store", "skill_root": str(self.workspace), "profile": "codex-acp-demo",
                       "timeout_seconds": 60, "canvas_url": "http://127.0.0.1:8000"}
        self.config_path, self.prompt_path = self.root / "config.json", self.root / "prompt.md"
        self.prompt_path.write_text("Use only the selected spec, role and stage.")
        self.env = {"AGENT_SERVER_URL": "http://127.0.0.1:18000", "SESSION_API_KEY": "secret-session",
                    "AUTOMATION_CALLBACK_URL": "http://127.0.0.1:18001/callback", "AUTOMATION_CALLBACK_API_KEY": "secret-callback",
                    "AUTOMATION_RUN_ID": str(uuid.uuid4()), "AUTOMATION_AGENT_PROFILE_ID": "not-the-fixed-profile"}
        self.set_event("apply", "SA")

    def spec_id(self, role, feature="first"):
        return f"{runner.ROLE_PREFIXES[role]}-REQ-006-{feature}"

    def change_path(self, spec_id=None):
        return self.store / "openspec/changes" / (spec_id or self.event["spec_id"])

    def task_path(self, spec_id=None):
        return self.change_path(spec_id) / "tasks.md"

    def create_spec(self, spec_id, role):
        root = self.change_path(spec_id)
        directory = root / "specs" / spec_id
        directory.mkdir(parents=True, exist_ok=True)
        (root / ".openspec.yaml").write_text("schema: " + runner.ROLE_SCHEMAS[role] + "\n")
        apps = [{"id": r.lower(), "name": r, "role": r, "repository": "https://github.com/example/" + r.lower() + ".git"} for r in ("Frontend", "Backend", "QA")]
        requirement = runner.role_change(spec_id)["requirement_id"]
        refs = [f"{runner.ROLE_PREFIXES[r]}-{requirement}-first" for r in runner.UPSTREAM_ROLES[role]]
        if not (root / "scope.json").exists():
            (root / "scope.json").write_text(json.dumps({"version": 1, "applications": apps if role == "SA" else [a for a in apps if a["role"] == role], "references": refs}))
        for file in ("proposal.md", "design.md"):
            (root / file).write_text("# Planning\n\nSelected role context.\n")
        (directory / "spec.md").write_text("# Spec\n\nSelected feature behavior.\n")
        path = self.task_path(spec_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Tasks\n- [ ] 1.1 [{role}] Implement and verify feature.\n")

    def set_event(self, stage, role, *, normalized=True, native=False, feature=None):
        self.config["stage"], self.config["role"] = stage, role
        self.config_path.write_text(json.dumps(self.config))
        selected = self.spec_id(role, feature or ("new-feature" if stage == "propose" else "first"))
        self.change = self.change_path(selected)
        self.event = {"schema": "openspec-role-dashboard/v3", "type": f"{stage}.requested", "stage": stage,
                      "approval": stage, "request_id": str(uuid.uuid4()), "spec_store": str(self.store),
                      "requirement_id": "REQ-006", "context_change": self.spec_id(role) if stage == "propose" else selected, "role": role,
                      "spec_id": selected, "change": selected, "request": "Add clear task context and tests" if stage != "apply" else ""}
        trigger = {"type": "event", "source": "openspec-role-dashboard", "on": f"{stage}.requested",
                   "filter": f"schema == 'openspec-role-dashboard/v3' && stage == '{stage}' && approval == '{stage}' && role == '{role}'"}
        if normalized:
            trigger.update(destination="dispatch_run", subject_key_expr=None, turn_text_expr=None, wake_agent=True)
        delivered = {"payload": self.event, "source_override": "openspec-role-dashboard", "event_key": f"{stage}.requested"} if native else self.event
        self.payload = {"trigger": "event", "trigger_payload": trigger, "event": delivered}
        self.write_event()
        return self.event

    def write_event(self):
        self.env["AUTOMATION_EVENT_PAYLOAD"] = json.dumps(self.payload)

    def fake_cli(self, config, *arguments):
        if arguments[:2] == ("store", "list"):
            return {"stores": [{"id": "fixture-store", "root": str(self.store)}]}
        self.assertIn("--store", arguments)
        self.assertEqual(arguments[arguments.index("--store") + 1], "fixture-store")
        if arguments[0] == "validate":
            return {"items": [{"id": config["change"], "valid": True}]}
        if arguments[0] == "status":
            return {"isPlanningComplete": True, "schemaName": runner.ROLE_SCHEMAS[config["role"]]}
        tasks = []
        for path in (self.change_path(config["change"]) / "tasks.md",):
            if not path.exists():
                continue
            for line, text in enumerate(path.read_text().splitlines(), 1):
                match = runner.TASK_LINE.match(text)
                if match:
                    tasks.append({"id": "1.1", "description": match.group(2), "done": (match.group(1) or '').lower() == "x",
                                  "sourcePath": str(path), "line": line})
        return {"tasks": tasks, "state": "ready"}

    def execute_action(self, config, prompt, **kwargs):
        self.assertNotIn("profile_id", kwargs)
        self.assertEqual(config["profile"], "codex-acp-demo")
        self.assertIn(config["spec_id"], prompt)
        result = dict(SUCCESS)
        if config["stage"] == "propose":
            self.create_spec(config["spec_id"], config["role"])
        elif config["stage"] == "update":
            (self.change / "specs" / config["spec_id"] / "spec.md").write_text("# Revised spec\n\nRequested clarification.\n")
        else:
            tasks = config["selected_tasks"]
            self.assertTrue(all(task["role"] == config["role"] and task["sourcePath"] == str(self.task_path(config["spec_id"])) for task in tasks))
            path = self.task_path(config["spec_id"])
            path.write_text(path.read_text().replace("[ ]", "[x]"))
            result["task_evidence"] = [{"task": task["description"], "evidence": "Required fixture scenario passed"} for task in tasks]
        return result

    def fake_git(self, arguments, *, cwd, timeout=120):
        if arguments[0] == "clone":
            (Path(arguments[-1]) / ".git").mkdir(parents=True)
            return ""
        if arguments[0] == "rev-parse":
            return cwd
        return "https://github.com/example/" + Path(cwd).name + ".git"

    def invoke(self, action=None, *, check=False):
        with mock.patch.object(runner, "git_command", side_effect=self.fake_git), \
                mock.patch.object(runner, "role_cli", side_effect=self.fake_cli), \
                mock.patch.object(runner.Path, "home", return_value=self.root), \
                mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback") as callback, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            client.return_value.run.side_effect = action or self.execute_action
            client.return_value.conversation_id = str(uuid.uuid4())
            code = runner.main(["--config", str(self.config_path), "--prompt", str(self.prompt_path), *(["--check"] if check else [])], env=self.env)
        return code, output.getvalue(), client, callback

    def test_all_twelve_actions_target_one_spec_and_preserve_siblings(self):
        for stage in runner.ROLE_STAGES:
            for role in runner.ROLES:
                with self.subTest(stage=stage, role=role):
                    self.create_spec(self.spec_id(role), role)
                    event = self.set_event(stage, role, native=True)
                    before = runner.scope_snapshot(self.store)
                    code, output, client, callback = self.invoke()
                    self.assertEqual(code, 0, output)
                    client.return_value.run.assert_called_once()
                    self.assertEqual(callback.call_args.args[0]["status"], "completed")
                    prefix = f"openspec/changes/{event['spec_id']}/"
                    allowed = {prefix + f"specs/{event['spec_id']}/spec.md", prefix + "tasks.md"}
                    if stage == "propose":
                        allowed.update(prefix + name for name in ("proposal.md", "design.md", ".openspec.yaml", "scope.json"))
                    self.assertFalse(self.metadata_path.exists())
                    self.assertLessEqual(runner.changed_paths(before, runner.scope_snapshot(self.store)), allowed)
                    self.assertEqual((self.workspace / "app.js").read_text(), "original implementation\n")

    def test_second_spec_can_reuse_task_ids_and_descriptions(self):
        self.set_event("apply", "Frontend", feature="second")
        before = self.task_path(self.spec_id("Frontend", "first")).read_bytes()
        code, output, _, _ = self.invoke()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.task_path(self.spec_id("Frontend", "first")).read_bytes(), before)
        self.assertIn("[x]", self.task_path().read_text())

    def test_raw_events_and_normalized_native_events_share_contract(self):
        for stage in runner.ROLE_STAGES:
            for role in runner.ROLES:
                event = self.set_event(stage, role, normalized=False)
                self.assertEqual(runner.require_role_trigger(self.env, self.config), event)
                self.set_event(stage, role, native=True)
                self.assertEqual(runner.require_role_trigger(self.env, self.config), self.event)

    def test_native_wrapper_rejects_wrong_routing_and_unknown_fields(self):
        for patch in ({"source_override": "other"}, {"event_key": "wrong"}, {"extra": True}, {"payload": None}):
            self.set_event("apply", "QA", native=True)
            self.payload["event"].update(patch)
            self.write_event()
            code, _, client, _ = self.invoke()
            self.assertEqual(code, 1)
            client.return_value.run.assert_not_called()

    def test_untrusted_envelopes_and_wrong_role_requirement_spec_are_rejected_early(self):
        patches = ({"schema": "openspec-role-dashboard/v1"}, {"profile": "evil"}, {"workspace": "/tmp"},
                   {"role": "Backend"}, {"approval": "propose"}, {"stage": "propose"}, {"change": "../escape"},
                   {"request_id": "../id"}, {"spec_store": "/another/store"}, {"context_change": "different"},
                   {"request": []}, {"requirement_id": "REQ-1"}, {"spec_id": "FE-REQ-006-first"},
                   {"spec_id": "SA-REQ-007-first"}, {"spec_id": "SA-REQ-006-../escape"})
        for patch in patches:
            with self.subTest(patch=patch):
                self.set_event("apply", "SA")
                self.event.update(patch)
                self.write_event()
                with mock.patch.object(runner, "role_preflight") as preflight:
                    code, _, client, _ = self.invoke()
                self.assertEqual(code, 1)
                preflight.assert_not_called()
                client.return_value.run.assert_not_called()

    def test_native_zero_input_run_and_nondefault_trigger_are_rejected(self):
        for alteration in ("missing-event", "manual", "wake_agent", "subject_key_expr", "destination", "extra"):
            self.set_event("apply", "Backend")
            if alteration == "missing-event":
                del self.payload["event"]
            elif alteration == "manual":
                self.payload["trigger_payload"]["source"] = "openspec-manual"
            else:
                self.payload["trigger_payload"][alteration] = "nondefault"
            self.write_event()
            code, _, client, _ = self.invoke()
            self.assertEqual(code, 1)
            client.return_value.run.assert_not_called()

    def test_propose_update_require_prompt_apply_accepts_empty(self):
        for stage in ("propose", "update"):
            self.set_event(stage, "SA")
            self.event["request"] = " "
            self.write_event()
            self.assertEqual(self.invoke()[0], 1)
        self.set_event("apply", "SA")
        self.assertEqual(self.invoke()[0], 0)

    def test_current_requirement_spec_association_and_store_registration_required(self):
        shutil.rmtree(self.change)
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("association has changed", output)
        client.return_value.run.assert_not_called()
        with mock.patch.object(runner, "role_cli", return_value={"stores": [{"id": "fixture-store", "root": "/different"}]}):
            with self.assertRaisesRegex(runner.RunError, "does not match"):
                runner.validate_role_store(self.config)

    def test_malformed_role_names_and_linked_changes_rejected(self):
        for name in ('SA-REQ-006-Invalid', 'FE-REQ-no-id-feature', 'fe-REQ-006-lowercase-role'):
            path = self.change.parent / name
            path.mkdir()
            self.assertEqual(self.invoke()[0], 1)
            path.rmdir()
        linked = self.change.parent / 'SA-REQ-006-linked'
        linked.symlink_to(self.workspace, target_is_directory=True)
        self.assertEqual(self.invoke()[0], 1)

    def test_replay_native_and_raw_cannot_start_second_agent(self):
        event = self.set_event("apply", "Frontend", native=True)
        self.assertEqual(self.invoke()[0], 0)
        self.payload["event"] = event
        self.write_event()
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("already consumed", output)
        client.return_value.run.assert_not_called()

    def test_both_locks_prevent_dispatch(self):
        for path in (self.workspace, self.store):
            with runner.workspace_lock(str(path)):
                code, output, client, _ = self.invoke()
            self.assertEqual(code, 1, output)
            self.assertIn("already using", output)
            client.return_value.run.assert_not_called()

    def test_propose_rejects_registered_or_unregistered_existing_artifacts(self):
        for feature in ("first", "unregistered"):
            self.set_event("propose", "Frontend", feature=feature)
            self.create_spec(self.event["spec_id"], "Frontend")
            code, output, client, _ = self.invoke()
            self.assertEqual(code, 1)
            self.assertIn("already exists", output)
            client.return_value.run.assert_not_called()

    def test_failed_propose_leaves_discoverable_folder_without_registry(self):
        self.set_event("propose", "SA")
        self.assertEqual(self.invoke(lambda *a, **k: {**SUCCESS, "status": "blocked"})[0], 1)
        self.assertFalse(self.metadata_path.exists())
        self.assertEqual((self.change / '.openspec.yaml').read_text(), 'schema: ' + runner.ROLE_SCHEMAS[self.config['role']] + '\n')
        self.assertIn(self.event['spec_id'], runner.read_role_changes(self.config))

    def test_planning_cannot_edit_siblings_configuration_or_implementation(self):
        sibling = self.change_path(self.spec_id('QA'))
        for target in (sibling / "proposal.md", sibling / "design.md", self.store / 'openspec/config.yaml',
                       self.workspace / "app.js", sibling / "specs" / self.spec_id("QA") / "spec.md"):
            self.set_event("update", "SA")
            before = target.read_bytes()
            def modify(config, prompt, **kwargs):
                target.write_text("forbidden change")
                return SUCCESS
            code, _, _, _ = self.invoke(modify)
            self.assertEqual(code, 1)
            target.write_bytes(before)

    def test_apply_cannot_edit_sibling_checkboxes_or_selected_task_text(self):
        for sibling in (True, False):
            self.set_event("apply", "SA")
            target = self.task_path(self.spec_id("SA", "second")) if sibling else self.task_path()
            before = target.read_bytes()
            def modify(config, prompt, **kwargs):
                target.write_text(target.read_text().replace("[ ]", "[x]") if sibling else target.read_text().replace("feature", "unplanned work"))
                return SUCCESS
            self.assertEqual(self.invoke(modify)[0], 1)
            target.write_bytes(before)

    def test_apply_requires_evidence_and_all_selected_tasks_complete(self):
        def no_evidence(config, prompt, **kwargs):
            return {**self.execute_action(config, prompt, **kwargs), "task_evidence": []}
        code, output, _, _ = self.invoke(no_evidence)
        self.assertEqual(code, 1)
        self.assertIn("without concrete task_evidence", output)
        self.set_event("apply", "QA")
        code, output, _, _ = self.invoke(lambda *args, **kwargs: SUCCESS)
        self.assertEqual(code, 1)
        self.assertIn("tasks remain unfinished", output)

    def test_update_propose_cannot_complete_tasks(self):
        for stage in ("propose", "update"):
            self.set_event(stage, "SA")
            def complete(config, prompt, **kwargs):
                if stage == "propose":
                    self.create_spec(config["spec_id"], config["role"])
                path = self.task_path(config["spec_id"])
                path.write_text(path.read_text().replace("[ ]", "[x]"))
                return SUCCESS
            self.assertEqual(self.invoke(complete)[0], 1)

    def test_blocked_or_findings_planning_cannot_mark_tasks_complete(self):
        for stage in ('propose', 'update'):
            for status in ('blocked', 'findings'):
                self.set_event(stage, 'SA', feature=f'new-{status}' if stage == 'propose' else 'first')
                def complete(config, prompt, **kwargs):
                    if stage == 'propose':
                        self.create_spec(config['spec_id'], config['role'])
                    path = self.task_path()
                    path.write_text(path.read_text().replace('[ ]', '[x]'))
                    return {'status': status, 'summary': 'Still waiting for the contract', 'findings': ['Unresolved design']}
                self.create_spec(self.spec_id('SA'), 'SA')
                code, output, _, _ = self.invoke(complete)
                self.assertEqual(code, 1, output)
                outcome = self.read_report()['outcome']
                self.assertEqual(outcome['status'], 'execution_error')
                self.assertEqual(outcome['summary'], 'Still waiting for the contract')
                self.assertTrue(outcome['audit_errors'])

    def test_missing_or_invalid_task_source_preserves_agent_blocker_and_audit(self):
        for action in ('delete', 'invalid-utf8'):
            self.create_spec(self.spec_id('SA'), 'SA')
            self.set_event('apply', 'SA')
            def corrupt(config, prompt, **kwargs):
                if action == 'delete':
                    self.task_path().unlink()
                else:
                    self.task_path().write_bytes(b'\xff')
                return {'status': 'blocked', 'summary': 'Backend still missing', 'findings': ['Need API'], 'blocker_type': 'dependency'}
            self.assertEqual(self.invoke(corrupt)[0], 1)
            outcome = self.read_report()['outcome']
            self.assertEqual(outcome['status'], 'execution_error')
            self.assertEqual(outcome['summary'], 'Backend still missing')
            self.assertEqual(outcome['findings'], ['Need API'])
            self.assertTrue(outcome['audit_errors'])

    def test_artifact_symlinks_missing_and_wrong_role_tasks_rejected(self):
        path = self.task_path()
        before = path.read_bytes()
        path.unlink()
        path.symlink_to(self.workspace / "app.js")
        self.assertEqual(self.invoke()[0], 1)
        path.unlink()
        path.write_text("# No tasks\n")
        self.assertEqual(self.invoke()[0], 1)
        path.write_bytes(before.replace(b"[SA]", b"[QA]"))
        self.assertEqual(self.invoke()[0], 1)

    def test_duplicate_local_task_numbers_cannot_be_proposed_or_updated(self):
        for stage in ("propose", "update"):
            for role_first in (False, True):
                self.set_event(stage, "SA", feature=("new-role-first" if role_first else "new-number-first") if stage == "propose" else "first")
                def duplicate(config, prompt, **kwargs):
                    if stage == "propose":
                        self.create_spec(config["spec_id"], config["role"])
                    first = "[SA] 1.1 First action" if role_first else "1.1 [SA] First action"
                    second = "[SA] 1.1 Different action" if role_first else "1.1 [SA] Different action"
                    self.task_path().write_text(f"- [ ] {first}\n- [ ] {second}\n")
                    return SUCCESS
                code, output, _, _ = self.invoke(duplicate)
                self.assertEqual(code, 1)
                self.assertIn("Duplicate task IDs", output)
                self.assertFalse(self.metadata_path.exists())
                if stage == "update":
                    self.create_spec(self.event["spec_id"], "SA")
                else:
                    shutil.rmtree(self.change)

    def test_wrong_schema_rejects_existing_change_actions_before_agent(self):
        original = self.fake_cli
        def wrong_schema(config, *arguments):
            return {"schemaName": "role-specs"} if arguments[0] == "status" else original(config, *arguments)
        with mock.patch.object(self, "fake_cli", side_effect=wrong_schema):
            for stage in ('update', 'apply'):
                self.set_event(stage, "SA")
                code, output, client, _ = self.invoke()
                self.assertEqual(code, 1)
                self.assertIn("schema must match", output)
                client.return_value.run.assert_not_called()

    def test_propose_cannot_complete_a_task_file_without_its_specification(self):
        self.set_event("propose", "SA")
        def task_only(config, prompt, **kwargs):
            self.task_path().write_text("- [ ] 1.1 [SA] A task without a spec\n")
            return SUCCESS
        code, output, _, _ = self.invoke(task_only)
        self.assertEqual(code, 1)
        self.assertIn("capability specifications", output)
        self.assertFalse(self.metadata_path.exists())

    def test_check_mode_does_not_consume_or_start(self):
        self.env.pop("AUTOMATION_EVENT_PAYLOAD")
        code, output, client, callback = self.invoke(check=True)
        self.assertEqual(code, 0, output)
        client.assert_not_called()
        callback.assert_not_called()
        self.assertFalse((self.root / ".openhands").exists())

    def test_non_req_prefix_and_short_numeric_id_are_routed_from_folders(self):
        self.create_spec('SA-STORY-12-first', 'SA')
        selected = 'FE-STORY-12-api'
        self.create_spec(selected, 'Frontend')
        self.set_event('apply', 'Frontend')
        self.event.update(requirement_id='STORY-12', spec_id=selected, change=selected, context_change=selected)
        self.change = self.change_path(selected)
        self.write_event()
        self.assertEqual(self.invoke()[0], 0)
        self.assertEqual(self.read_report()['requirement_id'], 'STORY-12')
        self.assertTrue(self.task_path(selected).read_text().count('[x]'))
        self.assertFalse(self.metadata_path.exists())

    def test_v2_event_is_rejected_even_when_it_uses_current_folder_names(self):
        self.event['schema'] = 'openspec-role-dashboard/v2'
        self.write_event()
        code, _, client, _ = self.invoke()
        self.assertEqual(code, 1)
        client.return_value.run.assert_not_called()

    def test_discovery_ignores_registry_archive_and_unrelated_changes(self):
        self.metadata_path.write_text('not even valid JSON; never read this')
        (self.change.parent / 'archive/SA-REQ-999-hidden').mkdir(parents=True)
        (self.change.parent / 'ordinary-change').mkdir()
        changes = runner.read_role_changes(self.config)
        self.assertEqual(len(changes), 8)
        self.assertEqual(self.invoke()[0], 0)
        self.assertEqual(self.metadata_path.read_text(), 'not even valid JSON; never read this')

    def test_untagged_standard_tasks_inherit_role_and_keep_evidence_checks(self):
        self.task_path().write_text('- [ ] 1.1 Implement and verify the contract.\n')
        code, output, _, _ = self.invoke()
        self.assertEqual(code, 0, output)
        self.assertIn('[x]', self.task_path().read_text())

    def test_short_role_tags_match_folder_roles_and_preserve_exact_evidence_descriptions(self):
        for role, alias in (("Frontend", "FE"), ("Backend", "BE")):
            for description in (f"1.1 [{alias}] Implement the contract.", f"[{alias}] 1.1 Implement the contract."):
                with self.subTest(role=role, description=description):
                    self.set_event("apply", role)
                    self.task_path().write_text(f"- [ ] {description}\n")
                    code, output, client, callback = self.invoke()
                    self.assertEqual(code, 0, output)
                    client.return_value.run.assert_called_once()
                    self.assertEqual(callback.call_args.args[0]["task_evidence"][0]["task"], description)

    def test_conflicting_leading_short_role_tags_are_rejected_before_agent_execution(self):
        for description in ("1.1 [FE] Implement a UI.", "[BE] 1.1 Implement an endpoint."):
            with self.subTest(description=description):
                self.set_event("apply", "SA")
                self.task_path().write_text(f"- [ ] {description}\n")
                code, output, client, _ = self.invoke()
                self.assertEqual(code, 1)
                self.assertIn("Explicit task tags must match", output)
                client.return_value.run.assert_not_called()

    def test_role_mentions_inside_task_prose_are_not_ownership_tags(self):
        for description in ("1.1 Document the [QA] badge and [BE] label.",
                            "[SA] 1.1 Review the [Frontend] interface."):
            with self.subTest(description=description):
                self.set_event("apply", "SA")
                self.task_path().write_text(f"- [ ] {description}\n")
                code, output, _, callback = self.invoke()
                self.assertEqual(code, 0, output)
                self.assertEqual(callback.call_args.args[0]["task_evidence"][0]["task"], description)

    def test_native_list_marker_variants_can_be_checked_with_evidence(self):
        for marker in ('1)', '1.', '+', '*', '-'):
            self.set_event('apply', 'SA')
            self.task_path().write_text(f'{marker}[ ] 1.1 Verify the contract.\n')
            code, output, _, _ = self.invoke()
            self.assertEqual(code, 0, output)
            self.assertIn('[x]', self.task_path().read_text())

    def test_propose_can_use_another_role_context_but_not_deleted_context(self):
        self.set_event('propose', 'Frontend')
        self.event['context_change'] = self.spec_id('SA')
        self.write_event()
        self.assertEqual(self.invoke()[0], 0)
        self.set_event('propose', 'Frontend', feature='another-feature')
        self.event['context_change'] = self.spec_id('SA')
        self.write_event()
        shutil.rmtree(self.change_path(self.spec_id('SA')))
        code, _, client, _ = self.invoke()
        self.assertEqual(code, 1)
        client.return_value.run.assert_not_called()
        self.assertFalse(self.change.exists())

    def test_update_repairs_partial_propose_artifacts_without_registry(self):
        self.set_event('propose', 'SA')
        self.assertEqual(self.invoke(lambda *args, **kwargs: {**SUCCESS, 'status': 'blocked'})[0], 1)
        self.set_event('update', 'SA', feature='new-feature')
        def repair(config, prompt, **kwargs):
            self.create_spec(config['spec_id'], config['role'])
            return SUCCESS
        code, output, _, _ = self.invoke(repair)
        self.assertEqual(code, 0, output)
        self.assertFalse(self.metadata_path.exists())

    def test_update_can_revise_own_proposal_and_design(self):
        self.set_event('update', 'SA')
        def revise(config, prompt, **kwargs):
            (self.change / 'proposal.md').write_text('# Revised motivation\n')
            (self.change / 'design.md').write_text('# Revised decisions\n')
            return SUCCESS
        self.assertEqual(self.invoke(revise)[0], 0)

    def test_planning_cannot_rewrite_schema_or_create_registry(self):
        for name in ('.openspec.yaml', 'registry'):
            self.set_event('update', 'SA')
            target = self.change / name if name != 'registry' else self.metadata_path
            before = target.read_bytes() if target.exists() else None
            def modify(config, prompt, **kwargs):
                target.write_text('unauthorized')
                return SUCCESS
            self.assertEqual(self.invoke(modify)[0], 1)
            if before is None:
                target.unlink()
            else:
                target.write_bytes(before)

    def test_role_change_limit_rejects_new_proposal_before_scaffold(self):
        for index in range(12):
            self.create_spec(self.spec_id('SA', f'additional-{index}'), 'SA')
        self.set_event('propose', 'SA')
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn('20 spec limit', output)
        client.return_value.run.assert_not_called()
        self.assertFalse(self.change.exists())

    def test_task_limit_is_shared_across_requirement_changes(self):
        self.task_path(self.spec_id('QA')).write_text(''.join(f'- [ ] {i} Task {i}\n' for i in range(501)))
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn('500 tasks across all role changes', output)
        client.return_value.run.assert_not_called()

    def test_cli_uses_pinned_binary_structured_arguments_and_fixed_cwd(self):
        with mock.patch.object(runner.subprocess, "run", return_value=mock.Mock(returncode=0, stdout=b'{"stores": []}')) as run:
            runner.role_cli(self.config, "store", "list", "--json")
        self.assertEqual(run.call_args.args[0], ["npx", "--no-install", "openspec", "store", "list", "--json"])
        self.assertEqual(run.call_args.kwargs["cwd"], str(self.store))
        self.assertNotIn("shell", run.call_args.kwargs)

    def read_report(self):
        return json.loads((self.root / '.openhands/apps/openspec-progress/role-results' /
                           (self.env['AUTOMATION_RUN_ID'] + '.json')).read_text())

    def test_reopening_checked_task_with_reason_preserves_dependency_blocker(self):
        path = self.task_path()
        path.write_text(path.read_text().replace('[ ]', '[x]'))
        def reopen(config, prompt, **kwargs):
            path.write_text(path.read_text().replace('[x]', '[ ]'))
            return {'status': 'blocked', 'summary': 'Backend label contract is missing',
                    'findings': ['UI cannot persist labels'], 'blocker_type': 'dependency',
                    'next_action': 'Implement Backend labels, then resubmit Frontend Apply.',
                    'task_corrections': [{'task': config['selected_tasks'][0]['description'], 'reason': 'No labels input or API exists'}]}
        code, _, _, callback = self.invoke(reopen)
        self.assertEqual(code, 1)
        self.assertEqual(callback.call_args.args[0]['summary'], 'Backend label contract is missing')
        outcome = self.read_report()['outcome']
        self.assertEqual((outcome['status'], outcome['blocker_type']), ('blocked', 'dependency'))
        self.assertEqual(outcome['audit_errors'], [])
        self.assertEqual(outcome['findings'], ['UI cannot persist labels'])

    def test_unexplained_reopening_preserves_original_result_and_specific_audit(self):
        path = self.task_path()
        path.write_text(path.read_text().replace('[ ]', '[x]'))
        def reopen(config, prompt, **kwargs):
            path.write_text(path.read_text().replace('[x]', '[ ]'))
            return {'status': 'blocked', 'summary': 'Backend contract is missing', 'findings': ['Need backend first']}
        code, _, _, callback = self.invoke(reopen)
        result = callback.call_args.args[0]
        self.assertEqual(code, 1)
        self.assertIn('task_corrections reason', result['audit_errors'][0])
        self.assertEqual(result['agent_result']['summary'], 'Backend contract is missing')
        outcome = self.read_report()['outcome']
        self.assertEqual(outcome['status'], 'execution_error')
        self.assertEqual(outcome['summary'], 'Backend contract is missing')
        self.assertEqual(outcome['agent_status'], 'blocked')

    def test_correction_reason_does_not_allow_text_changes_or_sibling_changes(self):
        for sibling in (False, True):
            self.set_event('apply', 'SA')
            target = self.task_path(self.spec_id('SA', 'second')) if sibling else self.task_path()
            before = target.read_text()
            def alter(config, prompt, **kwargs):
                target.write_text(before.replace('feature', 'unapproved scope'))
                return {'status': 'blocked', 'summary': 'Need input', 'findings': [],
                        'task_corrections': [{'task': config['selected_tasks'][0]['description'], 'reason': 'Not implemented'}]}
            self.assertEqual(self.invoke(alter)[0], 1)
            self.assertEqual(self.read_report()['outcome']['status'], 'execution_error')
            self.assertTrue(self.read_report()['outcome']['audit_errors'])
            target.write_text(before)

    def test_reopened_task_cannot_report_completed(self):
        path = self.task_path()
        path.write_text(path.read_text().replace('[ ]', '[x]'))
        def reopen(config, prompt, **kwargs):
            path.write_text(path.read_text().replace('[x]', '[ ]'))
            return {**SUCCESS, 'task_corrections': [{'task': config['selected_tasks'][0]['description'], 'reason': 'Evidence missing'}]}
        self.assertEqual(self.invoke(reopen)[0], 1)
        self.assertIn('remain unfinished', self.read_report()['outcome']['audit_errors'][0])

    def test_outcome_report_is_bound_private_bounded_and_redacted(self):
        def blocked(*args, **kwargs):
            return {'status': 'blocked', 'summary': 'secret-session ' + '长' * 3000,
                    'findings': ['secret-callback'] * 12, 'next_action': 'Read the conversation'}
        self.invoke(blocked)
        report = self.read_report()
        self.assertEqual(report['run_id'], self.env['AUTOMATION_RUN_ID'])
        self.assertEqual(report['spec_id'], self.event['spec_id'])
        self.assertEqual(report['role'], 'SA')
        self.assertEqual(report['configuration']['profile'], 'codex-acp-demo')
        self.assertEqual(len(report['outcome']['summary']), 2000)
        self.assertEqual(len(report['outcome']['findings']), 8)
        self.assertNotIn('secret-session', json.dumps(report))
        self.assertNotIn('secret-callback', json.dumps(report))
        path = self.root / '.openhands/apps/openspec-progress/role-results' / (report['run_id'] + '.json')
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)

    def test_report_failure_cannot_claim_success(self):
        with mock.patch.object(runner, 'save_role_outcome', side_effect=OSError('private error')):
            code, output, _, callback = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(callback.call_args.args[0]['outcome'], 'execution_error')
        self.assertNotIn('private error', output)

    def test_native_run_rejection_explains_kanban_without_starting_agent(self):
        self.env['AUTOMATION_EVENT_PAYLOAD'] = '{}'
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        client.assert_not_called()
        self.assertIn('OpenSpec Kanban', output)
        self.assertIn('matching role workflow', output)
        self.assertIn('Role spec and Automation', output)
        self.assertEqual(self.read_report()['outcome']['status'], 'needs_review')

    def test_report_writer_rejects_symlinks_and_invalid_run_ids(self):
        with mock.patch.object(runner.Path, 'home', return_value=self.root):
            with self.assertRaises(runner.RunError):
                runner.save_role_outcome(self.config, self.event, SUCCESS, {**self.env, 'AUTOMATION_RUN_ID': '../escape'}, None)
            root = self.root / '.openhands/apps/openspec-progress'
            root.mkdir(parents=True)
            (root / 'role-results').symlink_to(self.workspace, target_is_directory=True)
            with self.assertRaisesRegex(runner.RunError, 'symlinked'):
                runner.save_role_outcome(self.config, self.event, SUCCESS, self.env, None)

    # Exercise managed workspaces independently of the model/network.
    def test_sa_apply_rejects_code_changes_and_never_clones(self):
        def edit_code(config, prompt, **kwargs):
            self.assertTrue(config['workspace'].endswith('/planning'))
            (self.workspace / 'app.js').write_text('forbidden SA implementation')
            return self.execute_action(config, prompt, **kwargs)
        with mock.patch.object(self, 'fake_git', side_effect=AssertionError('SA must never clone')):
            code, output, _, _ = self.invoke(edit_code)
        self.assertEqual(code, 1)
        self.assertIn('SA changed implementation files', output)

    def test_downstream_conversation_and_report_use_bound_checkout(self):
        self.set_event('apply', 'Backend')
        expected = str(self.workspace / self.event['change'] / 'backend')
        def apply(config, prompt, **kwargs):
            self.assertEqual(config['workspace'], expected)
            self.assertEqual(config['scope']['references'], [self.spec_id('SA')])
            (Path(config['workspace']) / 'server.js').write_text('allowed implementation')
            return self.execute_action(config, prompt, **kwargs)
        code, output, _, _ = self.invoke(apply)
        self.assertEqual(code, 0, output)
        self.assertEqual(self.read_report()['configuration']['workspace'], expected)

    def test_downstream_cannot_edit_a_sibling_repository(self):
        self.set_event('apply', 'Backend')
        def apply(config, prompt, **kwargs):
            (self.workspace / 'app.js').write_text('wrong repository')
            return self.execute_action(config, prompt, **kwargs)
        code, output, _, _ = self.invoke(apply)
        self.assertEqual(code, 1)
        self.assertIn('another repository', output)

    def test_clone_failure_prevents_conversation_and_preserves_store(self):
        self.set_event('apply', 'Backend')
        before = runner.scope_snapshot(self.store)
        with mock.patch.object(self, 'fake_git', side_effect=runner.RunError('clone failed')):
            code, _, client, _ = self.invoke()
        self.assertEqual(code, 1)
        client.return_value.run.assert_not_called()
        self.assertEqual(before, runner.scope_snapshot(self.store))

    def test_scope_failures_prevent_clone_and_conversation(self):
        self.set_event('apply', 'QA')
        path = self.change / 'scope.json'
        original = path.read_text()
        for mutate in [lambda scope: scope['applications'].append(scope['applications'][0]),
                       lambda scope: scope['references'].pop(),
                       lambda scope: scope['references'].append('SA-OTHER-1-contract'),
                       lambda scope: scope['applications'][0].update(repository='https://secret@github.com/example/qa.git'),
                       lambda scope: scope['applications'][0].update(repository='file:///tmp/repo')]:
            scope = json.loads(original); mutate(scope); path.write_text(json.dumps(scope))
            with mock.patch.object(self, 'fake_git', side_effect=AssertionError('invalid scope must not clone')):
                code, _, client, _ = self.invoke()
            self.assertEqual(code, 1)
            client.return_value.run.assert_not_called()
        path.unlink()
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn('scope.json', output)
        client.return_value.run.assert_not_called()

    def test_real_git_clone_reuse_and_origin_mismatch(self):
        import subprocess
        source = self.root / 'source'
        source.mkdir()
        subprocess.run(['git', 'init', '-q', str(source)], check=True)
        (source / 'README.md').write_text('fixture')
        subprocess.run(['git', '-C', str(source), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(source), '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-qm', 'fixture'], check=True)
        self.set_event('apply', 'Backend')
        config = {**self.config, 'change': self.event['change'], 'scope': runner.read_scope(self.config, self.event['change'])}
        original = runner.git_command
        clones = []
        def local_clone(arguments, *, cwd, timeout=120):
            if arguments[0] == 'clone':
                clones.append(arguments)
                result = original(['clone', '--', str(source), arguments[-1]], cwd=cwd)
                original(['remote', 'set-url', 'origin', arguments[-2]], cwd=arguments[-1])
                return result
            return original(arguments, cwd=cwd, timeout=timeout)
        with mock.patch.object(runner, 'git_command', side_effect=local_clone):
            target = Path(runner.prepare_role_workspace(config))
            (target / 'unfinished.js').write_text('preserve user edits')
            again = {**self.config, 'change': self.event['change'], 'scope': config['scope']}
            self.assertEqual(runner.prepare_role_workspace(again), str(target))
            self.assertEqual((target / 'unfinished.js').read_text(), 'preserve user edits')
            self.assertEqual(len(clones), 1)
            original(['remote', 'set-url', 'origin', 'https://github.com/other/wrong.git'], cwd=str(target))
            with self.assertRaisesRegex(runner.RunError, 'origin does not match'):
                runner.prepare_role_workspace({**self.config, 'change': self.event['change'], 'scope': config['scope']})
            self.assertEqual((target / 'unfinished.js').read_text(), 'preserve user edits')

    def test_symlinked_checkout_fails_before_git(self):
        self.set_event('apply', 'Backend')
        config = {**self.config, 'change': self.event['change'], 'scope': runner.read_scope(self.config, self.event['change'])}
        directory = self.workspace / self.event['change']; directory.mkdir()
        (directory / 'backend').symlink_to(self.store)
        with mock.patch.object(runner, 'git_command') as git:
            with self.assertRaisesRegex(runner.RunError, 'symlink'):
                runner.prepare_role_workspace(config)
        git.assert_not_called()


if __name__ == "__main__":
    unittest.main()
