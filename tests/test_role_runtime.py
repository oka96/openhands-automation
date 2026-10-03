"""Role dispatch contracts with real temporary stores and a fake agent/CLI."""

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
SUCCESS = {"status": "completed", "summary": "Verified the selected role action", "findings": [], "task_evidence": []}


class RoleRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.workspace = self.root / "workspace"
        self.store = self.root / "store"
        (self.workspace / "openspec").mkdir(parents=True)
        (self.workspace / "app.js").write_text("original implementation\n")
        for skill in set(runner.STAGES.values()):
            directory = self.workspace / ".agents/skills" / skill
            directory.mkdir(parents=True)
            (directory / "SKILL.md").write_text("Use the selected OpenSpec skill.")
        self.change = self.store / "openspec/changes/example-change"
        self.create_artifacts(self.change)
        self.metadata = {"version": 1, "name": "Fixtures", "description": "Tests", "requirements": [{
            "id": "REQ-006", "title": "Example", "summary": "Fixture", "change": "example-change",
            "roles": {role: {"owner": "Fixture", "state": "backlog", "note": ""} for role in runner.ROLES}}]}
        self.metadata_path = self.store / "openspec/requirements.json"
        self.metadata_path.write_text(json.dumps(self.metadata))
        self.config = {"mode": "role", "stage": "apply", "workspace": str(self.workspace), "spec_store": str(self.store),
                       "store_id": "fixture-store", "skill_root": str(self.workspace), "profile": "codex-acp-demo",
                       "timeout_seconds": 60, "canvas_url": "http://127.0.0.1:8000"}
        self.config_path = self.root / "config.json"
        self.prompt_path = self.root / "prompt.md"
        self.prompt_path.write_text("Use only the selected role and stage.")
        self.env = {"AGENT_SERVER_URL": "http://127.0.0.1:18000", "SESSION_API_KEY": "secret-session",
                    "AUTOMATION_CALLBACK_URL": "http://127.0.0.1:18001/callback", "AUTOMATION_CALLBACK_API_KEY": "secret-callback",
                    "AUTOMATION_RUN_ID": "run-id", "AUTOMATION_AGENT_PROFILE_ID": "not-the-fixed-profile"}
        self.set_event("apply", "SA")

    def create_artifacts(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "proposal.md").write_text("# Proposal\n\nDeliver a useful feature.\n")
        (directory / "design.md").write_text("# Design\n\nFour role delivery.\n")
        (directory / "tasks.md").write_text("# Tasks\n" + "".join(
            f"- [ ] {i}.1 [{role}] Implement and verify {role} work.\n" for i, role in enumerate(runner.ROLES, 1)))

    def set_event(self, stage, role, *, normalized=True, native=False):
        self.config["stage"], self.config["role"] = stage, role
        self.config_path.write_text(json.dumps(self.config))
        event = {"schema": "openspec-role-dashboard/v1", "type": f"{stage}.requested", "stage": stage,
                 "approval": stage, "request_id": str(uuid.uuid4()), "spec_store": str(self.store),
                 "requirement_id": "REQ-006", "context_change": "example-change", "role": role,
                 "change": f"new-{role.lower()}-change" if stage == "propose" else "example-change",
                 "request": "Add clear task context and tests" if stage != "apply" else ""}
        trigger = {"type": "event", "source": "openspec-role-dashboard", "on": f"{stage}.requested",
                   "filter": f"schema == 'openspec-role-dashboard/v1' && stage == '{stage}' && approval == '{stage}' && role == '{role}'"}
        if normalized:
            trigger.update({"destination": "dispatch_run", "subject_key_expr": None, "turn_text_expr": None, "wake_agent": True})
        delivered = {"payload": event, "source_override": "openspec-role-dashboard", "event_key": f"{stage}.requested"} if native else event
        self.payload = {"trigger": "event", "trigger_payload": trigger, "event": delivered}
        self.write_event()
        return event

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
            return {"isPlanningComplete": True}
        path = self.store / "openspec/changes" / config["change"] / "tasks.md"
        tasks = []
        for line, text in enumerate(path.read_text().splitlines(), 1):
            match = re.fullmatch(r"- \[([ x])\] (.*)", text)
            if match:
                tasks.append({"id": str(len(tasks) + 1), "description": match.group(2), "done": match.group(1) == "x",
                              "sourcePath": str(path), "line": line})
        return {"tasks": tasks, "state": "ready"}

    def execute_action(self, config, prompt, **kwargs):
        self.assertNotIn("profile_id", kwargs)
        self.assertEqual(config["profile"], "codex-acp-demo")
        self.assertIn(config["role"], prompt)
        path = self.store / "openspec/changes" / config["change"]
        result = dict(SUCCESS)
        if config["stage"] == "propose":
            self.create_artifacts(path)
        elif config["stage"] == "update":
            (path / "proposal.md").write_text("# Revised proposal\n\nRequested clarification.\n")
        else:
            tasks = config["selected_tasks"]
            self.assertTrue(all(task["role"] == config["role"] for task in tasks))
            lines = (path / "tasks.md").read_text().splitlines(keepends=True)
            for task in tasks:
                lines[task["line"] - 1] = lines[task["line"] - 1].replace("[ ]", "[x]", 1)
            (path / "tasks.md").write_text("".join(lines))
            result["task_evidence"] = [{"task": task["description"], "evidence": "Required fixture scenario passed"} for task in tasks]
        return result

    def invoke(self, action=None, *, check=False):
        with mock.patch.object(runner, "role_cli", side_effect=self.fake_cli), \
                mock.patch.object(runner.Path, "home", return_value=self.root), \
                mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback") as callback, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            client.return_value.run.side_effect = action or self.execute_action
            code = runner.main(["--config", str(self.config_path), "--prompt", str(self.prompt_path), *( ["--check"] if check else [])], env=self.env)
        return code, output.getvalue(), client, callback

    def test_fixed_role_rejects_another_valid_role_before_starting_agent(self):
        self.payload["event"]["role"] = "Backend"
        self.write_event()
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1, output)
        client.assert_not_called()

    def test_all_twelve_role_action_combinations_preserve_boundaries_and_fixed_profile(self):
        for stage in runner.ROLE_STAGES:
            for role in runner.ROLES:
                with self.subTest(stage=stage, role=role):
                    self.create_artifacts(self.change)
                    event = self.set_event(stage, role, native=True)
                    before = self.metadata_path.read_text()
                    code, output, client, callback = self.invoke()
                    self.assertEqual(code, 0, output)
                    client.return_value.run.assert_called_once()
                    self.assertEqual(callback.call_args.args[0]["status"], "completed")
                    self.assertEqual((self.workspace / "app.js").read_text(), "original implementation\n")
                    if stage == "propose":
                        metadata = json.loads(self.metadata_path.read_text())
                        proposed = metadata["requirements"][-1]
                        self.assertEqual(proposed["change"], event["change"])
                        self.assertEqual(set(proposed["roles"]), set(runner.ROLES))
                        self.assertEqual(proposed["title"], event["request"])
                    else:
                        self.assertEqual(self.metadata_path.read_text(), before)
                    if stage == "apply":
                        lines = (self.change / "tasks.md").read_text().splitlines()[1:]
                        self.assertEqual(sum("[x]" in line for line in lines), 1)
                        self.assertIn(f"[{role}]", next(line for line in lines if "[x]" in line))

    def test_raw_role_event_compatibility_for_all_twelve_combinations(self):
        for stage in runner.ROLE_STAGES:
            for role in runner.ROLES:
                with self.subTest(stage=stage, role=role):
                    event = self.set_event(stage, role)
                    self.assertEqual(runner.require_role_trigger(self.env, self.config), event)

    def test_native_wrapper_rejects_wrong_routing_unknown_fields_and_invalid_inner_event(self):
        mutations = (
            lambda wrapper: wrapper.update(source_override="other-source"),
            lambda wrapper: wrapper.update(event_key="update.requested"),
            lambda wrapper: wrapper.update(unknown="not-allowed"),
            lambda wrapper: wrapper.pop("source_override"),
            lambda wrapper: wrapper.pop("event_key"),
            lambda wrapper: wrapper.update(payload=None),
            lambda wrapper: wrapper.update(payload=[]),
            lambda wrapper: wrapper["payload"].update(stage="update"),
            lambda wrapper: wrapper["payload"].update(profile="not-an-input"),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.set_event("apply", "QA", native=True)
                mutation(self.payload["event"])
                self.write_event()
                with mock.patch.object(runner, "role_preflight") as preflight:
                    code, output, client, _ = self.invoke()
                self.assertEqual(code, 1, output)
                preflight.assert_not_called()
                client.return_value.run.assert_not_called()

    def test_native_and_raw_delivery_share_the_same_replay_guard(self):
        event = self.set_event("apply", "Frontend", native=True)
        code, output, _, _ = self.invoke()
        self.assertEqual(code, 0, output)
        self.payload["event"] = event
        self.write_event()
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("already consumed", output)
        client.return_value.run.assert_not_called()

    def test_untrusted_envelopes_are_rejected_before_store_preflight(self):
        event = dict(self.payload["event"])
        for patch in ({"profile": "evil"}, {"workspace": "/tmp"}, {"role": "Owner"}, {"approval": "propose"},
                      {"stage": "propose"}, {"change": "../escape"}, {"request_id": "../id"}, {"spec_store": "/another/store"},
                      {"context_change": "different"}, {"request": []}, {"requirement_id": "../metadata"}):
            with self.subTest(patch=patch):
                self.payload["event"] = {**event, **patch}
                self.write_event()
                with mock.patch.object(runner, "role_preflight") as preflight:
                    code, output, client, callback = self.invoke()
                self.assertEqual(code, 1, output)
                preflight.assert_not_called()
                client.return_value.run.assert_not_called()
                self.assertEqual(callback.call_args.args[0]["status"], "blocked")

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
            code, output, client, _ = self.invoke()
            self.assertEqual(code, 1, output)
            client.return_value.run.assert_not_called()

    def test_propose_update_require_prompt_apply_accepts_empty(self):
        for stage in ("propose", "update"):
            self.set_event(stage, "SA")
            self.payload["event"]["request"] = " "
            self.write_event()
            code, _, client, _ = self.invoke()
            self.assertEqual(code, 1)
            client.return_value.run.assert_not_called()
        self.set_event("apply", "SA", normalized=False)
        self.assertEqual(self.invoke()[0], 0)

    def test_current_metadata_association_and_store_registration_are_required(self):
        self.metadata["requirements"][0]["change"] = "renamed-change"
        self.metadata_path.write_text(json.dumps(self.metadata))
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("association has changed", output)
        client.return_value.run.assert_not_called()
        with mock.patch.object(runner, "role_cli", return_value={"stores": [{"id": "fixture-store", "root": "/different"}]}):
            with self.assertRaisesRegex(runner.RunError, "does not match"):
                runner.validate_role_store(self.config)

    def test_replay_cannot_start_a_second_agent(self):
        self.assertEqual(self.invoke()[0], 0)
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("already consumed", output)
        client.return_value.run.assert_not_called()

    def test_both_workspace_and_store_locks_prevent_dispatch(self):
        for path in (self.workspace, self.store):
            with runner.workspace_lock(str(path)):
                code, output, client, _ = self.invoke()
            self.assertEqual(code, 1, output)
            self.assertIn("already using", output)
            client.return_value.run.assert_not_called()

    def test_existing_proposal_is_rejected_without_agent(self):
        event = self.set_event("propose", "Frontend")
        self.create_artifacts(self.store / "openspec/changes" / event["change"])
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("already exists", output)
        client.return_value.run.assert_not_called()

    def test_propose_allocates_stable_next_id_only_after_valid_artifacts(self):
        self.set_event("propose", "QA")
        code, output, _, _ = self.invoke()
        self.assertEqual(code, 0, output)
        self.assertEqual(json.loads(self.metadata_path.read_text())["requirements"][-1]["id"], "REQ-007")
        self.set_event("propose", "SA")
        before = self.metadata_path.read_bytes()
        code, _, _, _ = self.invoke(lambda *args, **kwargs: {**SUCCESS, "status": "blocked", "summary": "Missing scope decision"})
        self.assertEqual(code, 1)
        self.assertEqual(self.metadata_path.read_bytes(), before)

    def test_planning_cannot_modify_implementation_or_unrelated_store_files(self):
        self.set_event("update", "QA")
        def modify_workspace(config, prompt, **kwargs):
            (self.workspace / "app.js").write_text("forbidden")
            return SUCCESS
        code, output, _, _ = self.invoke(modify_workspace)
        self.assertEqual(code, 1)
        self.assertIn("changed implementation", output)
        self.set_event("update", "SA")
        def modify_metadata(config, prompt, **kwargs):
            self.metadata_path.write_text("{}")
            return SUCCESS
        code, output, _, _ = self.invoke(modify_metadata)
        self.assertEqual(code, 1)
        self.assertIn("permitted store scope", output)

    def test_apply_cannot_check_other_roles_or_edit_task_descriptions(self):
        def wrong_role(config, prompt, **kwargs):
            path = self.change / "tasks.md"
            path.write_text(path.read_text().replace("- [ ] 2.1", "- [x] 2.1"))
            return SUCCESS
        code, output, _, _ = self.invoke(wrong_role)
        self.assertEqual(code, 1)
        self.assertIn("another role", output)
        self.set_event("apply", "SA")
        def rewrite(config, prompt, **kwargs):
            path = self.change / "tasks.md"
            path.write_text(path.read_text().replace("SA work", "unplanned SA work"))
            return SUCCESS
        code, output, _, _ = self.invoke(rewrite)
        self.assertEqual(code, 1)
        self.assertIn("task text", output)

    def test_apply_requires_evidence_and_all_selected_tasks_complete(self):
        def no_evidence(config, prompt, **kwargs):
            result = self.execute_action(config, prompt, **kwargs)
            result["task_evidence"] = []
            return result
        code, output, _, _ = self.invoke(no_evidence)
        self.assertEqual(code, 1)
        self.assertIn("without concrete task_evidence", output)
        self.create_artifacts(self.change)
        self.set_event("apply", "QA")
        code, output, _, _ = self.invoke(lambda *args, **kwargs: SUCCESS)
        self.assertEqual(code, 1)
        self.assertIn("tasks remain unfinished", output)

    def test_update_and_propose_cannot_complete_role_tasks(self):
        for stage in ("propose", "update"):
            self.create_artifacts(self.change)
            self.set_event(stage, "SA")
            def complete_task(config, prompt, **kwargs):
                if stage == "propose":
                    self.create_artifacts(self.store / "openspec/changes" / config["change"])
                path = self.store / "openspec/changes" / config["change"] / "tasks.md"
                path.write_text(path.read_text().replace("[ ]", "[x]", 1))
                return SUCCESS
            code, output, _, _ = self.invoke(complete_task)
            self.assertEqual(code, 1, output)
            self.assertEqual(len(json.loads(self.metadata_path.read_text())["requirements"]), 1)

    def test_artifact_symlinks_and_missing_role_tasks_are_rejected(self):
        task_path = self.change / "tasks.md"
        task_path.unlink()
        task_path.symlink_to(self.workspace / "app.js")
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("symlinks", output)
        client.return_value.run.assert_not_called()
        task_path.unlink()
        task_path.write_text("- [ ] 1.1 [SA] Only one role.\n")
        code, output, client, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("nonempty SA", output)
        client.return_value.run.assert_not_called()

    def test_check_mode_validates_store_without_consuming_or_starting(self):
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
