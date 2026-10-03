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
                    "AUTOMATION_CALLBACK_API_KEY": "callback-secret", "AUTOMATION_RUN_ID": "run-id"}

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

    def test_idle_does_not_count_as_finished_and_timeout_pauses(self):
        server = FakeServer(["idle"] * 40)
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(runner.RunError, "timed out"):
            self.client(server).run(self.config, "prompt")
        self.assertEqual(server.now, 30)
        self.assertFalse(any(path.endswith("/agent_final_response") for path, _ in server.calls))
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
        with mock.patch.object(runner, "Client") as client, mock.patch.object(runner, "fire_callback") as callback:
            code, output = self.invoke("--check")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["status"], "valid")
        client.assert_not_called()
        callback.assert_not_called()

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
