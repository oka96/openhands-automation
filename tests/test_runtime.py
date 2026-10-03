"""Contract and failure-path tests; no live agents or credentials required."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error


SPEC = importlib.util.spec_from_file_location("runner", Path(__file__).parents[1] / "runtime" / "run.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
SUCCESS = {"status": "completed", "summary": "Checks passed", "findings": []}


class FakeServer:
    def __init__(self, states=None, final=None, failure=None):
        self.calls = []
        self.states = iter(states or ["finished"])
        self.last_state = "running"
        self.final = json.dumps(SUCCESS) if final is None else final
        self.failure = failure
        self.now = 0

    def sleep(self, seconds):
        self.now += seconds

    def request(self, url, **kwargs):
        path = urllib_path(url)
        self.calls.append((path, kwargs))
        if path == self.failure:
            raise runner.RunError("Simulated transport failure")
        if path == "/api/agent-profiles":
            return {"profiles": [{"name": "codex-acp-demo", "id": "profile-id"}]}
        if path == "/api/settings":
            return {"conversation_settings": {"confirmation_mode": True, "security_analyzer": "llm"}}
        if path == "/api/conversations":
            return {"id": kwargs["body"]["conversation_id"]}
        if path.startswith("/api/conversations/") and kwargs.get("method") == "PATCH":
            return {"success": True}
        if path.endswith("/events") and kwargs.get("method") == "POST":
            return {"success": True}
        if path.endswith("/pause"):
            return {}
        if path.endswith("/agent_final_response"):
            return {"response": self.final}
        if path.startswith("/api/conversations/"):
            self.last_state = next(self.states, self.last_state)
            return {"execution_status": self.last_state}
        if path == "/callback":
            return {}
        raise AssertionError(f"Unexpected path {path}")


def urllib_path(url):
    return runner.urllib.parse.urlsplit(url).path


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        (self.workspace / "openspec" / "changes" / "example-change").mkdir(parents=True)
        for skill in set(runner.STAGES.values()):
            directory = self.workspace / ".agents" / "skills" / skill
            directory.mkdir(parents=True)
            (directory / "SKILL.md").write_text("Use OpenSpec")
        self.config = {"workspace": str(self.workspace), "stage": "verify", "change": "example-change",
                       "profile": "codex-acp-demo", "request": "", "timeout_seconds": 60,
                       "canvas_url": "http://127.0.0.1:8002"}
        self.config_path = self.root / "config.json"
        self.write_config()
        self.prompt_path = self.root / "prompt.md"
        self.prompt_path.write_text("Review the selected change. Return terminal JSON.")
        self.env = {"AGENT_SERVER_URL": "http://127.0.0.1:18020", "SESSION_API_KEY": "session-secret",
                    "AUTOMATION_CALLBACK_URL": "http://127.0.0.1:18021/callback",
                    "AUTOMATION_CALLBACK_API_KEY": "callback-secret", "AUTOMATION_RUN_ID": "run-id",
                    "AUTOMATION_EVENT_PAYLOAD": json.dumps({"trigger": "event", "trigger_payload": {
                        "type": "event", "source": "openspec-manual", "on": "manual-only", "filter": "`false`"},
                        "automation_id": "automation-id", "automation_name": "OpenSpec Verify"})}

    def write_config(self):
        self.config_path.write_text(json.dumps(self.config))

    def client(self, server):
        return runner.Client(self.env["AGENT_SERVER_URL"], self.env["SESSION_API_KEY"],
                             requester=server.request, clock=lambda: server.now, sleep=server.sleep)

    def invoke(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = runner.main(["--config", str(self.config_path), "--prompt", str(self.prompt_path), *args], env=self.env)
        return code, output.getvalue()

    def test_config_refuses_missing_request_or_existing_proposal(self):
        self.config["stage"] = "propose"
        self.write_config()
        with self.assertRaisesRegex(runner.RunError, "concrete request"):
            runner.load_config(self.config_path)
        self.config["request"] = "Build task filters"
        self.write_config()
        with self.assertRaisesRegex(runner.RunError, "already exists"):
            runner.load_config(self.config_path)
        self.config["change"] = "new-change"
        self.write_config()
        self.assertEqual(runner.load_config(self.config_path)["stage"], "propose")

    def test_config_refuses_path_traversal_and_missing_active_change(self):
        for name, expected in (("../escape", "kebab-case"), ("missing-change", "does not exist")):
            self.config["change"] = name
            self.write_config()
            with self.assertRaisesRegex(runner.RunError, expected):
                runner.load_config(self.config_path)

    def test_config_requires_existing_skill_and_absolute_workspace(self):
        self.config["workspace"] = "relative"
        self.write_config()
        with self.assertRaisesRegex(runner.RunError, "absolute"):
            runner.load_config(self.config_path)
        self.config["workspace"] = str(self.workspace)
        (self.workspace / ".agents/skills/openspec-apply-change/SKILL.md").unlink()
        self.write_config()
        with self.assertRaisesRegex(runner.RunError, "missing.*skill"):
            runner.load_config(self.config_path)

    def test_local_url_refuses_remote_credentials_and_extra_url_parts(self):
        for url in ("https://example.com", "http://localHost.attacker", "http://a:b@localhost",
                    "http://localhost/?token=x", "http://localhost/path", "http://localhost:bad", "file:///tmp/a"):
            with self.subTest(url=url), self.assertRaises(runner.RunError):
                runner.local_url(url)
        self.assertEqual(runner.local_url("http://[::1]:8000/"), "http://[::1]:8000")

    def test_security_policy_mapping_preserves_explicit_policy(self):
        policy = {"kind": "ConfirmRisky", "threshold": "LOW", "confirm_unknown": True}
        result = runner.conversation_options({"confirmation_policy": policy, "security_analyzer": "pattern"})
        self.assertEqual(result["confirmation_policy"], policy)
        self.assertEqual(result["security_analyzer"], {"kind": "PatternSecurityAnalyzer"})
        self.assertEqual(runner.conversation_options({"confirmation_mode": True})["confirmation_policy"], {"kind": "AlwaysConfirm"})
        self.assertEqual(runner.conversation_options({"confirmation_mode": True, "security_analyzer": "llm"})["confirmation_policy"]["kind"], "ConfirmRisky")
        with self.assertRaises(runner.RunError):
            runner.conversation_options({"confirmation_policy": {"kind": "Unknown"}})

    def test_terminal_result_fails_closed(self):
        self.assertEqual(runner.terminal_result("```json\n" + json.dumps(SUCCESS) + "\n```"), SUCCESS)
        for value in ("Everything passed", json.dumps({**SUCCESS, "findings": ["bug"]}),
                      json.dumps({"status": "completed", "summary": "ok"}),
                      json.dumps(SUCCESS) + "\nHowever a test then failed",
                      "```json\n" + json.dumps(SUCCESS) + "\n```\nMore text",
                      json.dumps({**SUCCESS, "status": "success"})):
            with self.subTest(value=value), self.assertRaises(runner.RunError):
                runner.terminal_result(value)

    def test_terminal_result_accepts_acp_commentary_before_final_json(self):
        for suffix in (json.dumps(SUCCESS), "```json\n" + json.dumps(SUCCESS) + "\n```",
                       "```\n" + json.dumps(SUCCESS) + "\n```"):
            self.assertEqual(runner.terminal_result("I am checking the tests.\nThey passed.\n" + suffix), SUCCESS)
        finding = {"status": "findings", "summary": "One test failed", "findings": ["failure"]}
        self.assertEqual(runner.terminal_result(json.dumps(SUCCESS) + "\n" + json.dumps(finding)), finding)

    def test_timeout_cannot_exceed_local_service_limit(self):
        self.config["timeout_seconds"] = 1801
        self.write_config()
        with self.assertRaisesRegex(runner.RunError, "1800"):
            runner.load_config(self.config_path)

    def test_conversation_creation_uses_local_workspace_profile_and_policy(self):
        server = FakeServer(["running", "finished"])
        with contextlib.redirect_stdout(io.StringIO()):
            result = self.client(server).run(self.config, "stage prompt", run_id="run-id")
        self.assertEqual(result, SUCCESS)
        body = next(kwargs["body"] for path, kwargs in server.calls if path == "/api/conversations")
        self.assertEqual(body["agent_profile_id"], "profile-id")
        self.assertEqual(body["workspace"], {"kind": "LocalWorkspace", "working_dir": str(self.workspace)})
        self.assertFalse(body["worktree"])
        self.assertTrue(body["initial_message"]["run"])
        self.assertEqual(body["confirmation_policy"]["kind"], "ConfirmRisky")
        self.assertEqual(body["tags"]["automationrunid"], "run-id")
        self.assertFalse(any(path.endswith("/pause") for path, _ in server.calls))

    def test_selected_profile_id_skips_name_lookup(self):
        server = FakeServer()
        with contextlib.redirect_stdout(io.StringIO()):
            self.client(server).run(self.config, "prompt", profile_id="selected-profile")
        self.assertFalse(any(path == "/api/agent-profiles" for path, _ in server.calls))
        body = next(kwargs["body"] for path, kwargs in server.calls if path == "/api/conversations")
        self.assertEqual(body["agent_profile_id"], "selected-profile")

    def test_role_conversations_use_plain_spec_title_before_execution_and_reduced_tags_for_every_role_and_stage(self):
        for stage in ("propose", "update", "apply"):
            for role in ("SA", "Frontend", "Backend", "QA"):
                with self.subTest(stage=stage, role=role):
                    server = FakeServer()
                    config = {**self.config, "mode": "role", "stage": stage, "role": role,
                              "requirement_id": "REQ-006", "context_change": "context-change",
                              "change": "context-change", "spec_id": f"{runner.ROLE_PREFIXES[role]}-REQ-006-feature"}
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.client(server).run(config, "role prompt", run_id="role-run-id")
                    body = next(kwargs["body"] for path, kwargs in server.calls if path == "/api/conversations")
                    self.assertFalse(body["autotitle"])
                    self.assertIsNone(body["initial_message"])
                    mutations = [(path, call) for path, call in server.calls if call.get("method") in ("POST", "PATCH")]
                    self.assertEqual([call["method"] for _, call in mutations], ["POST", "PATCH", "POST"])
                    conversation_path = "/api/conversations/" + body["conversation_id"]
                    self.assertEqual(mutations[1][0], conversation_path)
                    self.assertEqual(mutations[1][1]["body"], {"title": config["spec_id"]})
                    self.assertEqual(mutations[2][0], conversation_path + "/events")
                    self.assertEqual(mutations[2][1]["body"], {
                        "role": "user", "content": [{"type": "text", "text": "role prompt"}], "run": True})
                    self.assertEqual(body["tags"], {
                        "requirement": "REQ-006", "role": role, "openspecstage": stage,
                        "openspecspec": config["spec_id"],
                        "automationrunid": "role-run-id", "automationtrigger": "automation"})

    def test_role_naming_failure_never_starts_agent(self):
        for outcome in ("transport", "rejected"):
            with self.subTest(outcome=outcome):
                server = FakeServer()
                request = server.request
                def failing_title(url, **kwargs):
                    if kwargs.get("method") == "PATCH":
                        server.calls.append((urllib_path(url), kwargs))
                        if outcome == "transport":
                            raise runner.RunError("Title update response lost")
                        return {"success": False}
                    return request(url, **kwargs)
                client = runner.Client("http://127.0.0.1:18000", "secret", requester=failing_title,
                                       clock=lambda: server.now, sleep=server.sleep)
                config = {**self.config, "mode": "role", "role": "SA", "requirement_id": "REQ-006", "spec_id": "SA-REQ-006-feature"}
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(runner.RunError):
                    client.run(config, "role prompt")
                self.assertFalse(any(path.endswith("/events") or path.endswith("/run") for path, _ in server.calls))
                created = next(call['body'] for path, call in server.calls if path == '/api/conversations')
                self.assertIsNone(created['initial_message'])
                self.assertTrue(server.calls[-1][0].endswith("/pause"))

    def test_legacy_conversations_omit_obsolete_tags_and_preserve_stage_and_origin(self):
        for stage in ("explore", "propose", "update", "apply", "verify", "sync", "archive"):
            with self.subTest(stage=stage):
                server = FakeServer()
                with contextlib.redirect_stdout(io.StringIO()):
                    self.client(server).run({**self.config, "stage": stage}, "stage prompt", run_id="legacy-run-id")
                body = next(kwargs["body"] for path, kwargs in server.calls if path == "/api/conversations")
                self.assertEqual(body["tags"], {
                    "openspecstage": stage,
                    "automationrunid": "legacy-run-id", "automationtrigger": "automation"})

    def test_idle_does_not_count_as_finished_and_timeout_pauses(self):
        server = FakeServer(["idle"] * 40)
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(runner.RunError, "timed out"):
            self.client(server).run(self.config, "prompt")
        self.assertEqual(server.now, 30)
        self.assertFalse(any(path.endswith("/agent_final_response") for path, _ in server.calls))
        self.assertTrue(server.calls[-1][0].endswith("/pause"))

    def test_role_preflight_time_counts_toward_deadline_and_reserves_postflight(self):
        server = FakeServer(["running"] * 40)
        server.now = 15
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(runner.RunError, "timed out"):
            self.client(server).run({**self.config, "mode": "role", "requirement_id": "REQ-006", "role": "SA", "spec_id": "SA-REQ-006-feature"},
                                    "role prompt", deadline=60)
        self.assertEqual(server.now, 30)
        self.assertTrue(server.calls[-1][0].endswith("/pause"))

    def test_waiting_for_confirmation_and_invalid_final_pause(self):
        for server, expected in ((FakeServer(["waiting_for_confirmation"]), "requires attention"),
                                 (FakeServer(final="ordinary prose"), "terminal JSON")):
            with self.subTest(expected=expected), contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(runner.RunError, expected):
                self.client(server).run(self.config, "prompt")
            self.assertTrue(server.calls[-1][0].endswith("/pause"))

    def test_create_transport_failure_attempts_pause(self):
        server = FakeServer(failure="/api/conversations")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(runner.RunError, "transport"):
            self.client(server).run(self.config, "prompt")
        self.assertTrue(server.calls[-1][0].endswith("/pause"))

    def test_interruption_pauses_running_conversation(self):
        server = FakeServer(["running"])
        client = self.client(server)
        client.sleep = mock.Mock(side_effect=KeyboardInterrupt)
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
            client.run(self.config, "prompt")
        self.assertTrue(server.calls[-1][0].endswith("/pause"))

    def test_lock_rejects_concurrent_run_and_releases_after_error(self):
        with runner.workspace_lock(str(self.workspace)):
            with self.assertRaisesRegex(runner.RunError, "already using"):
                with runner.workspace_lock(str(self.workspace)):
                    self.fail("A concurrent run acquired the same workspace")
        with runner.workspace_lock(str(self.workspace)):
            pass

    def test_callback_records_failure_and_conversation(self):
        server = FakeServer()
        finding = {"status": "findings", "summary": "A test failed", "findings": ["test failure"]}
        runner.fire_callback(finding, self.env, conversation_id="conversation-id", requester=server.request)
        body = server.calls[-1][1]["body"]
        self.assertEqual(body, {"status": "FAILED", "run_id": "run-id", "conversation_id": "conversation-id", "error": "A test failed"})
        runner.fire_callback(SUCCESS, self.env, requester=server.request)
        self.assertEqual(server.calls[-1][1]["body"]["status"], "COMPLETED")

    def test_check_mode_performs_no_api_calls_or_callback(self):
        self.env.pop("AUTOMATION_EVENT_PAYLOAD")
        with mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback") as callback:
            code, output = self.invoke("--check")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["status"], "valid")
        client.assert_not_called()
        callback.assert_not_called()

    def test_manual_run_trigger_starts_conversation(self):
        with mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback") as callback:
            client.return_value.run.return_value = SUCCESS
            code, output = self.invoke()
        self.assertEqual(code, 0)
        client.return_value.run.assert_called_once()
        self.assertEqual(callback.call_args.args[0]["status"], "completed")

    def dashboard_event(self):
        self.config["stage"] = "explore"
        self.write_config()
        event = {"schema": "openspec-dashboard/v1", "type": "explore.requested", "stage": "explore",
                 "approval": "explore", "request_id": "e02ae0d2-d0ba-4561-b856-78b91588928c",
                 "workspace": str(self.workspace), "change": "new-requirement",
                 "request": "Explore 标签 and keyboard access", "parameters": {"focus": "accessibility", "limit": 3}}
        payload = {"trigger": "event", "trigger_payload": {
            "type": "event", "source": "openspec-dashboard", "on": "explore.requested",
            "filter": "schema == 'openspec-dashboard/v1' && stage == 'explore' && approval == 'explore'"}, "event": event}
        self.env["AUTOMATION_EVENT_PAYLOAD"] = json.dumps(payload)
        return payload

    def test_dashboard_inputs_reach_existing_runner_without_changing_shared_config(self):
        self.dashboard_event()
        before = self.config_path.read_bytes()
        with mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback"), \
                mock.patch.object(runner, "claim_dashboard_request") as claim:
            client.return_value.run.return_value = SUCCESS
            code, output = self.invoke()
        self.assertEqual(code, 0)
        claim.assert_called_once()
        config, prompt = client.return_value.run.call_args.args
        self.assertEqual(config["change"], "new-requirement")
        self.assertEqual(config["parameters"], {"focus": "accessibility", "limit": 3})
        self.assertEqual(config["profile"], "codex-acp-demo")
        self.assertIn("new-requirement", prompt)
        self.assertEqual(self.config_path.read_bytes(), before)

    def test_dashboard_source_keeps_native_manual_run_defaults(self):
        payload = self.dashboard_event()
        del payload["event"]
        self.env["AUTOMATION_EVENT_PAYLOAD"] = json.dumps(payload)
        self.assertIsNone(runner.require_manual_trigger(self.env, runner.load_config(self.config_path)))

    def test_dashboard_parameter_limit_uses_compact_json(self):
        payload = self.dashboard_event()
        payload["event"]["parameters"] = {"items": [0] * 3500}
        self.env["AUTOMATION_EVENT_PAYLOAD"] = json.dumps(payload)
        self.assertEqual(runner.require_manual_trigger(self.env, runner.load_config(self.config_path)), payload["event"])
        for params in ({"items": [0] * 4500}, {"invalid": float("nan")}):
            payload["event"]["parameters"] = params
            self.env["AUTOMATION_EVENT_PAYLOAD"] = json.dumps(payload)
            with self.assertRaises(runner.RunError):
                runner.require_manual_trigger(self.env, runner.load_config(self.config_path))

    def test_dashboard_cannot_override_stage_workspace_profile_or_replay(self):
        valid = self.dashboard_event()
        invalid = [
            {**valid, "event": {**valid["event"], "stage": "apply"}},
            {**valid, "event": {**valid["event"], "workspace": "/another"}},
            {**valid, "event": {**valid["event"], "profile": "another"}},
            {**valid, "event": {**valid["event"], "change": "../../etc"}},
            {**valid, "event": {**valid["event"], "request_id": "../path"}},
            {**valid, "event": {**valid["event"], "parameters": []}},
        ]
        for payload in invalid:
            self.env["AUTOMATION_EVENT_PAYLOAD"] = json.dumps(payload)
            with self.assertRaises(runner.RunError):
                runner.require_manual_trigger(self.env, runner.load_config(self.config_path))
        self.env["AUTOMATION_EVENT_PAYLOAD"] = json.dumps(valid)
        with self.assertRaises(runner.RunError):
            runner.require_manual_trigger(self.env, {**runner.load_config(self.config_path), "stage": "apply"})
        consumed = self.root / "consumed"
        runner.claim_dashboard_request(valid["event"], consumed)
        with self.assertRaisesRegex(runner.RunError, "already consumed"):
            runner.claim_dashboard_request(valid["event"], consumed)

    def test_missing_malformed_scheduled_and_delivered_events_cannot_start_agent(self):
        manual = json.loads(self.env["AUTOMATION_EVENT_PAYLOAD"])
        invalid = [None, "not-json", "[]", "{}", json.dumps({**manual, "trigger": "cron"}),
                   json.dumps({**manual, "event": {"action": "dispatch"}}),
                   json.dumps({**manual, "event": None}),
                   json.dumps({**manual, "trigger_payload": {"type": "event", "source": "github", "on": "manual-only"}}),
                   json.dumps({**manual, "trigger_payload": {"type": "event", "source": "openspec-manual", "on": "other"}}),
                   json.dumps({**manual, "trigger_payload": {"type": "event", "source": "openspec-manual", "on": "manual-only"}}),
                   json.dumps({**manual, "trigger_payload": {**manual["trigger_payload"], "filter": "`true`"}})]
        for payload in invalid:
            with self.subTest(payload=payload):
                if payload is None:
                    self.env.pop("AUTOMATION_EVENT_PAYLOAD", None)
                else:
                    self.env["AUTOMATION_EVENT_PAYLOAD"] = payload
                with mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback") as callback:
                    code, output = self.invoke()
                self.assertEqual(code, 1)
                client.assert_not_called()
                self.assertEqual(callback.call_args.args[0]["status"], "blocked")

    def test_preflight_failure_fires_failed_callback_without_starting_agent(self):
        self.config["stage"] = "update"
        self.write_config()
        with mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback") as callback:
            code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(callback.call_args.args[0]["status"], "blocked")
        client.assert_not_called()

    def test_completed_run_callback_failure_is_nonzero(self):
        with mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback", side_effect=runner.RunError("callback down")):
            client.return_value.run.return_value = SUCCESS
            code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("Completion callback failed", output)

    def test_interruption_fires_failed_callback(self):
        with mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback") as callback:
            client.return_value.run.side_effect = KeyboardInterrupt
            code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertEqual(callback.call_args.args[0]["status"], "blocked")
        self.assertIn("interrupted", output)

    def test_final_output_redacts_injected_credentials(self):
        with mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback") as callback:
            client.return_value.run.return_value = {**SUCCESS, "summary": "session-secret callback-secret"}
            code, output = self.invoke()
        self.assertEqual(code, 0)
        self.assertNotIn("session-secret", output)
        self.assertNotIn("callback-secret", output)
        self.assertEqual(callback.call_args.args[0]["summary"], "[redacted] [redacted]")

    def test_http_errors_never_echo_secret_response_bodies(self):
        error = urllib.error.HTTPError("http://localhost", 500, "secret-response", {}, io.BytesIO(b"api-key-secret"))
        opener = mock.Mock()
        opener.open.side_effect = error
        with mock.patch.object(runner.urllib.request, "build_opener", return_value=opener):
            with self.assertRaisesRegex(runner.RunError, "HTTP 500") as raised:
                runner.request_json("http://localhost/api/settings")
        self.assertNotIn("secret", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
