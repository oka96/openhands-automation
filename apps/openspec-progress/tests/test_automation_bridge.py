import hashlib
import hmac
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location("automation_bridge", Path(__file__).resolve().parents[1] / "src/automation_bridge.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
AUTO = "1db988df-a508-4201-aa7c-3090c9c33256"
RUN = "846a4b28-837f-4e78-9cfc-e580e55c45ad"
ORG = "9c3e29b0-d420-4e62-a29d-6e13df9fd543"
REQUEST = "3d7a8f15-8dcd-4a64-bc57-6f86da7096c5"


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.patch = mock.patch.object(bridge.Path, "home", return_value=self.home)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.service = {"url_from_agent": "http://127.0.0.1:18021", "api_prefix": "/api/automation", "auth_env_var": "OPENHANDS_AUTOMATION_API_KEY"}
        self.auto = {"id": AUTO, "name": bridge.NAME, "trigger": bridge.FIELDS, "state": "ACTIVE", "enabled": True}
        self.calls = []
        self.failed_event = False
        self.others = []
        self.client = bridge.Bridge(self.service, str(self.home), env={"OPENHANDS_AUTOMATION_API_KEY": "private-key"}, requester=self.request)

    def request(self, url, **options):
        self.calls.append((url, options))
        if url.endswith("?limit=100") and "/webhooks" not in url:
            return {"automations": [self.auto, *self.others], "total": 1 + len(self.others)}
        if url.endswith("/webhooks?limit=100"):
            return {"webhooks": [], "total": 0}
        if url.endswith("/webhooks"):
            return {"source": bridge.SOURCE, "org_id": ORG}
        if "/events/" in url:
            if self.failed_event:
                raise bridge.BridgeError("Response lost")
            return {"received": True, "matched": 1, "runs_created": [RUN]}
        raise AssertionError(url)

    def data(self):
        return {"automation_id": AUTO, "request_id": REQUEST, "workspace": str(self.home), "change": "new-change",
                "request": "Explore 标签; $(do-not-run)", "parameters": {"focus": "keyboard", "limit": 3}}

    def test_probe_is_read_only_and_setup_keeps_secret_off_the_wire_to_canvas(self):
        self.assertFalse(self.client.probe()["ready"])
        self.assertFalse(self.client.root.exists())
        result = self.client.setup()
        self.assertTrue(result["ready"])
        self.assertNotIn("secret", json.dumps(result))
        config = self.client.config()
        self.assertTrue(config["secret"])
        self.assertEqual((self.client.root / "connection.json").stat().st_mode & 0o777, 0o600)
        self.client.setup()
        self.assertEqual(sum(url.endswith("/webhooks") for url, _ in self.calls), 1)

    def test_signed_input_is_per_run_and_repeating_same_id_does_not_dispatch_again(self):
        self.client.setup()
        before = json.dumps(self.auto, sort_keys=True)
        result = self.client.dispatch(self.data())
        self.assertEqual(result["run_id"], RUN)
        self.assertEqual(self.client.dispatch(self.data()), result)
        events = [(url, options) for url, options in self.calls if "/events/" in url]
        self.assertEqual(len(events), 1)
        raw = events[0][1]["body"]
        event = json.loads(raw)
        self.assertEqual(event["request"], self.data()["request"])
        self.assertEqual(event["parameters"], self.data()["parameters"])
        self.assertNotIn("automation_id", event)
        expected = "sha256=" + hmac.new(self.client.config()["secret"].encode(), raw, hashlib.sha256).hexdigest()
        self.assertEqual(events[0][1]["headers"], {"X-Signature-256": expected})
        self.assertEqual(json.dumps(self.auto, sort_keys=True), before)

    def test_uncertain_dispatch_is_never_automatically_retried(self):
        self.client.setup()
        self.failed_event = True
        with self.assertRaises(bridge.BridgeError):
            self.client.dispatch(self.data())
        with self.assertRaisesRegex(bridge.BridgeError, "may already"):
            self.client.dispatch(self.data())
        self.assertEqual(sum("/events/" in url for url, _ in self.calls), 1)

    def test_reused_id_with_different_inputs_and_ambiguous_routing_are_rejected(self):
        self.client.setup()
        self.client.dispatch(self.data())
        with self.assertRaisesRegex(bridge.BridgeError, "different inputs"):
            self.client.dispatch({**self.data(), "request": "Different"})
        self.others = [{**self.auto, "id": RUN, "name": "Another automation"}]
        with self.assertRaisesRegex(bridge.BridgeError, "More than one"):
            self.client.dispatch(self.data())

    def test_remote_address_auth_changes_and_home_escape_are_rejected(self):
        for service in ({**self.service, "url_from_agent": "https://example.com"},
                        {**self.service, "url_from_agent": "http://user:pass@localhost"},
                        {**self.service, "auth_env_var": "OTHER_SECRET"},
                        {**self.service, "api_prefix": "/another"}):
            with self.assertRaises(bridge.BridgeError):
                bridge.Bridge(service, str(self.home), env={"OPENHANDS_AUTOMATION_API_KEY": "private-key"})
        with self.assertRaises(bridge.BridgeError):
            bridge.Bridge(self.service, "/another", env={"OPENHANDS_AUTOMATION_API_KEY": "private-key"})

    def test_invalid_params_and_inputs_never_dispatch(self):
        self.client.setup()
        for change in ({"change": "../bad"}, {"request": ""}, {"parameters": []},
                       {"parameters": {"huge": "x" * 8192}}, {"stage": "apply"}, {"request_id": "bad"}):
            with self.assertRaises(bridge.BridgeError):
                self.client.dispatch({**self.data(), **change})
        self.assertFalse(any("/events/" in url for url, _ in self.calls))


if __name__ == "__main__":
    unittest.main()
