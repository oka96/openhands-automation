"""Role/spec dispatch contracts with real temporary stores and a fake agent/CLI."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
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
        self.change = self.store / "openspec/changes/example-change"
        self.change.mkdir(parents=True)
        for file in ("proposal.md", "design.md"):
            (self.change / file).write_text("# Shared planning\n\nPreserve this context.\n")
        self.metadata = {"version": 2, "name": "Fixtures", "description": "Tests", "requirements": [{
            "id": "REQ-006", "title": "Example", "summary": "Fixture", "change": "example-change",
            "roles": {role: {"owner": "Fixture", "note": "", "specs": [self.entry(role, feature) for feature in ("first", "second")]}
                      for role in runner.ROLES}}]}
        for role in runner.ROLES:
            for feature in ("first", "second"):
                self.create_spec(self.spec_id(role, feature), role)
        self.metadata_path = self.store / "openspec/requirements.json"
        self.save_metadata()
        self.config = {"mode": "role", "stage": "apply", "workspace": str(self.workspace), "spec_store": str(self.store),
                       "store_id": "fixture-store", "skill_root": str(self.workspace), "profile": "codex-acp-demo",
                       "timeout_seconds": 60, "canvas_url": "http://127.0.0.1:8000"}
        self.config_path, self.prompt_path = self.root / "config.json", self.root / "prompt.md"
        self.prompt_path.write_text("Use only the selected spec, role and stage.")
        self.env = {"AGENT_SERVER_URL": "http://127.0.0.1:18000", "SESSION_API_KEY": "secret-session",
                    "AUTOMATION_CALLBACK_URL": "http://127.0.0.1:18001/callback", "AUTOMATION_CALLBACK_API_KEY": "secret-callback",
                    "AUTOMATION_RUN_ID": "run-id", "AUTOMATION_AGENT_PROFILE_ID": "not-the-fixed-profile"}
        self.set_event("apply", "SA")

    def spec_id(self, role, feature="first"):
        return f"{runner.ROLE_PREFIXES[role]}-REQ-006-{feature}"

    def entry(self, role, feature):
        return {"id": self.spec_id(role, feature), "title": feature.title(), "state": "backlog", "note": ""}

    def task_path(self, spec_id=None):
        return self.change / "tasks" / ((spec_id or self.event["spec_id"]) + ".md")

    def save_metadata(self):
        self.metadata_path.write_text(json.dumps(self.metadata))

    def create_spec(self, spec_id, role):
        directory = self.change / "specs" / spec_id
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "spec.md").write_text("# Spec\n\nSelected feature behavior.\n")
        path = self.task_path(spec_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Tasks\n- [ ] 1.1 [{role}] Implement and verify feature.\n")

    def set_event(self, stage, role, *, normalized=True, native=False, feature=None):
        self.config["stage"], self.config["role"] = stage, role
        self.config_path.write_text(json.dumps(self.config))
        self.event = {"schema": "openspec-role-dashboard/v2", "type": f"{stage}.requested", "stage": stage,
                      "approval": stage, "request_id": str(uuid.uuid4()), "spec_store": str(self.store),
                      "requirement_id": "REQ-006", "context_change": "example-change", "role": role,
                      "spec_id": self.spec_id(role, feature or ("new-feature" if stage == "propose" else "first")),
                      "change": "example-change", "request": "Add clear task context and tests" if stage != "apply" else ""}
        trigger = {"type": "event", "source": "openspec-role-dashboard", "on": f"{stage}.requested",
                   "filter": f"schema == 'openspec-role-dashboard/v2' && stage == '{stage}' && approval == '{stage}' && role == '{role}'"}
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
            return {"isPlanningComplete": True, "schemaName": "role-specs"}
        tasks = []
        for path in sorted((self.change / "tasks").glob("*.md")):
            for line, text in enumerate(path.read_text().splitlines(), 1):
                match = re.fullmatch(r"- \[([ x])\] (.*)", text)
                if match:
                    tasks.append({"id": "1.1", "description": match.group(2), "done": match.group(1) == "x",
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

    def invoke(self, action=None, *, check=False):
        with mock.patch.object(runner, "role_cli", side_effect=self.fake_cli), \
                mock.patch.object(runner.Path, "home", return_value=self.root), \
                mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback") as callback, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            client.return_value.run.side_effect = action or self.execute_action
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
                    allowed = {f"openspec/changes/example-change/specs/{event['spec_id']}/spec.md",
                               f"openspec/changes/example-change/tasks/{event['spec_id']}.md"}
                    if stage == "propose":
                        allowed.add("openspec/requirements.json")
                        metadata = json.loads(self.metadata_path.read_text())
                        self.assertEqual(len(metadata["requirements"]), 1)
                        self.assertEqual(metadata["requirements"][0]["id"], "REQ-006")
                        self.assertEqual(metadata["requirements"][0]["roles"][role]["specs"][-1]["id"], event["spec_id"])
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
        self.metadata["requirements"][0]["roles"]["SA"]["specs"].pop(0)
        self.save_metadata()
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("association has changed", output)
        client.return_value.run.assert_not_called()
        with mock.patch.object(runner, "role_cli", return_value={"stores": [{"id": "fixture-store", "root": "/different"}]}):
            with self.assertRaisesRegex(runner.RunError, "does not match"):
                runner.validate_role_store(self.config)

    def test_metadata_version_duplicates_and_wrong_ownership_rejected(self):
        original = json.loads(json.dumps(self.metadata))
        for mutation in (lambda m: m.update(version=1),
                         lambda m: m["requirements"][0]["roles"]["SA"]["specs"].append(self.entry("SA", "first")),
                         lambda m: m["requirements"][0]["roles"]["SA"]["specs"][0].update(id=self.spec_id("Backend"))):
            self.metadata = json.loads(json.dumps(original))
            mutation(self.metadata)
            self.save_metadata()
            code, _, client, _ = self.invoke()
            self.assertEqual(code, 1)
            client.return_value.run.assert_not_called()

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

    def test_failed_propose_preserves_metadata(self):
        self.set_event("propose", "SA")
        before = self.metadata_path.read_bytes()
        self.assertEqual(self.invoke(lambda *a, **k: {**SUCCESS, "status": "blocked"})[0], 1)
        self.assertEqual(self.metadata_path.read_bytes(), before)

    def test_planning_cannot_edit_shared_sibling_metadata_or_implementation(self):
        for target in (self.change / "proposal.md", self.change / "design.md", self.metadata_path,
                       self.workspace / "app.js", self.change / "specs" / self.spec_id("QA") / "spec.md"):
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
                before = self.metadata_path.read_bytes()
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
                self.assertEqual(self.metadata_path.read_bytes(), before)
                if stage == "update":
                    self.create_spec(self.event["spec_id"], "SA")
                else:
                    self.task_path().unlink()
                    directory = self.change / "specs" / self.event["spec_id"]
                    (directory / "spec.md").unlink()
                    directory.rmdir()

    def test_wrong_schema_rejects_all_stages_before_agent(self):
        original = self.fake_cli
        def wrong_schema(config, *arguments):
            return {"schemaName": "spec-driven"} if arguments[0] == "status" else original(config, *arguments)
        with mock.patch.object(self, "fake_cli", side_effect=wrong_schema):
            for stage in runner.ROLE_STAGES:
                self.set_event(stage, "SA")
                code, output, client, _ = self.invoke()
                self.assertEqual(code, 1)
                self.assertIn("role-specs schema", output)
                client.return_value.run.assert_not_called()

    def test_propose_cannot_register_a_task_file_without_its_specification(self):
        self.set_event("propose", "SA")
        before = self.metadata_path.read_bytes()
        def task_only(config, prompt, **kwargs):
            self.task_path().write_text("- [ ] 1.1 [SA] A task without a spec\n")
            return SUCCESS
        code, output, _, _ = self.invoke(task_only)
        self.assertEqual(code, 1)
        self.assertIn("nonempty specification", output)
        self.assertEqual(self.metadata_path.read_bytes(), before)

    def test_check_mode_does_not_consume_or_start(self):
        self.env.pop("AUTOMATION_EVENT_PAYLOAD")
        code, output, client, callback = self.invoke(check=True)
        self.assertEqual(code, 0, output)
        client.assert_not_called()
        callback.assert_not_called()
        self.assertFalse((self.root / ".openhands").exists())

    def test_cli_uses_pinned_binary_structured_arguments_and_fixed_cwd(self):
        with mock.patch.object(runner.subprocess, "run", return_value=mock.Mock(returncode=0, stdout=b'{"stores": []}')) as run:
            runner.role_cli(self.config, "store", "list", "--json")
        self.assertEqual(run.call_args.args[0], ["npx", "--no-install", "openspec", "store", "list", "--json"])
        self.assertEqual(run.call_args.kwargs["cwd"], str(self.workspace))
        self.assertNotIn("shell", run.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
