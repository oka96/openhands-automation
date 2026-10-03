"""Fixed local bridge for explicit, parameterized Explore automation requests.

Runs inside the Agent Server. Credentials never leave this process. There is no
listener or daemon: Canvas calls this bounded helper through its Bash adapter.
"""
import base64
import contextlib
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid

SOURCE = "openspec-dashboard"
NAME = "OpenSpec 01 · Explore"
FILTER = "schema == 'openspec-dashboard/v1' && stage == 'explore' && approval == 'explore'"
FIELDS = {"type": "event", "source": SOURCE, "on": "explore.requested", "filter": FILTER}


class BridgeError(Exception):
    pass


def require(value, message):
    if not value:
        raise BridgeError(message)


def identifier(value):
    try:
        return isinstance(value, str) and str(uuid.UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, *, method="GET", body=None, headers=None):
    raw = body if isinstance(body, bytes) else None if body is None else encode(body)
    request = urllib.request.Request(url, data=raw, method=method,
                                    headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=5) as response:
            result = response.read(1_000_001)
        require(len(result) <= 1_000_000, "Automation response exceeded its size limit")
        return json.loads(result)
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        raise BridgeError(f"Automation request failed (HTTP {status})") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise BridgeError("Automation request failed or returned invalid data") from None


def atomic_json(path, value):
    descriptor, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encode(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path):
    if not path.exists():
        return None
    require(path.is_file() and not path.is_symlink(), "Bridge state is not a regular file")
    require(path.stat().st_size < 65536, "Bridge state exceeded its size limit")
    return json.loads(path.read_text())


class Bridge:
    def __init__(self, service, home, *, env=None, requester=request_json):
        env = os.environ if env is None else env
        require(isinstance(service, dict), "Automation runtime service is not available on this backend")
        origin = service.get("url_from_agent", "")
        try:
            parsed = urllib.parse.urlsplit(origin)
            parsed.port
        except (ValueError, TypeError):
            raise BridgeError("Invalid Automation service address") from None
        require(parsed.scheme in ("http", "https") and parsed.hostname in ("localhost", "127.0.0.1", "::1")
                and not parsed.username and not parsed.password and parsed.path in ("", "/")
                and not parsed.query and not parsed.fragment, "Only the advertised local Automation service is supported")
        require(service.get("api_prefix") == "/api/automation"
                and service.get("auth_env_var") == "OPENHANDS_AUTOMATION_API_KEY",
                "Unsupported Automation authentication or API prefix")
        self.key = env.get("OPENHANDS_AUTOMATION_API_KEY")
        require(isinstance(self.key, str) and self.key, "Agent Server has no injected Automation key; use the native local Canvas launcher")
        require(isinstance(home, str) and Path(home).is_absolute() and Path(home).resolve() == Path.home().resolve(),
                "Agent Server home does not match the helper's local home")
        self.base = origin.rstrip("/") + "/api/automation/v1"
        self.root = Path(home) / ".openhands/apps/openspec-progress/automation" / hashlib.sha256(self.base.encode()).hexdigest()[:16]
        self.requester = requester

    def api(self, path, *, method="GET", body=None):
        return self.requester(self.base + path, method=method, body=body,
                              headers={"X-Session-API-Key": self.key})

    def automation(self, expected_id=None):
        inventory = self.api("?limit=100")
        require(isinstance(inventory, dict) and isinstance(inventory.get("automations"), list)
                and isinstance(inventory.get("total"), int) and inventory["total"] <= 100,
                "Cannot inspect the complete Automation inventory (maximum 100 definitions)")
        matches = [item for item in inventory["automations"] if isinstance(item, dict) and item.get("name") == NAME]
        require(len(matches) == 1 and identifier(matches[0].get("id")), "The existing Explore automation is missing or ambiguous")
        item = matches[0]
        require(expected_id is None or item["id"] == expected_id, "The selected Explore automation changed; reconnect before running")
        return item

    def ready_automation(self, item):
        trigger = item.get("trigger", {})
        require(isinstance(trigger, dict) and all(trigger.get(key) == value for key, value in FIELDS.items())
                and trigger.get("destination", "dispatch_run") == "dispatch_run"
                and item.get("state") == "ACTIVE" and item.get("enabled") is True,
                "Sync the updated Explore definition before using dashboard inputs")

    def config(self):
        return read_json(self.root / "connection.json")

    def probe(self):
        item = self.automation()
        try:
            self.ready_automation(item)
            config = self.config()
            ready = bool(config and config.get("state") == "ready")
            message = "Connected to the existing Explore automation." if ready else "Connect Explore once to enable signed local requests."
        except BridgeError as error:
            ready, message = False, str(error)
        return {"kind": "probe", "ready": ready, "message": message,
                "automation": {"id": item["id"], "name": NAME}}

    @contextlib.contextmanager
    def lock(self):
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        require(not self.root.is_symlink(), "Bridge state directory must not be a symlink")
        with (self.root / ".lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise BridgeError("Another Explore request is being processed; check its result first") from None
            yield

    def setup(self):
        item = self.automation()
        self.ready_automation(item)
        with self.lock():
            config = self.config()
            if config and config.get("state") == "ready":
                return {"kind": "setup", "ready": True, "automation": {"id": item["id"], "name": NAME}}
            require(config is None, "An earlier connection attempt has an unknown outcome; inspect the local connection state before retrying")
            existing = self.api("/webhooks?limit=100")
            require(isinstance(existing, dict) and isinstance(existing.get("webhooks"), list)
                    and existing.get("total", 101) <= 100, "Cannot inspect the complete local source inventory")
            require(not any(row.get("source") == SOURCE for row in existing["webhooks"]),
                    "The dashboard source already exists without a saved local connection; do not overwrite its secret")
            config = {"state": "registering", "secret": secrets.token_urlsafe(32)}
            atomic_json(self.root / "connection.json", config)
            created = self.api("/webhooks", method="POST", body={
                "name": "OpenSpec dashboard · explicit Explore requests", "source": SOURCE,
                "event_key_expr": "type", "signature_header": "X-Signature-256",
                "signature_scheme": "hmac_sha256_hex", "webhook_secret": config["secret"],
            })
            require(isinstance(created, dict) and identifier(created.get("org_id")) and created.get("source") == SOURCE,
                    "Source creation returned unexpected data; inspect the local connection state")
            config.update(state="ready", org_id=created["org_id"])
            atomic_json(self.root / "connection.json", config)
        return {"kind": "setup", "ready": True, "automation": {"id": item["id"], "name": NAME}}

    def dispatch(self, data):
        fields = {"automation_id", "request_id", "workspace", "change", "request", "parameters"}
        require(isinstance(data, dict) and set(data) == fields, "Unexpected Explore input fields")
        require(identifier(data["automation_id"]) and identifier(data["request_id"]), "Invalid automation or request ID")
        require(isinstance(data["workspace"], str) and Path(data["workspace"]).is_absolute()
                and "\x00" not in data["workspace"] and "\n" not in data["workspace"], "Workspace must be an absolute local directory")
        require(isinstance(data["change"], str) and len(data["change"]) <= 100
                and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", data["change"]), "Change must be a kebab-case name")
        require(isinstance(data["request"], str) and data["request"].strip() and len(data["request"]) <= 10000,
                "Enter an Explore prompt of at most 10000 characters")
        require(isinstance(data["parameters"], dict) and len(encode(data["parameters"])) <= 8192,
                "Parameters must be a JSON object of at most 8 KiB")
        item = self.automation(data["automation_id"])
        self.ready_automation(item)
        # Refuse ambiguous routing before sending an event. No shared definition
        # is changed for a run; each event carries its own immutable input.
        inventory = self.api("?limit=100")
        require(not any(row.get("id") != item["id"] and row.get("enabled")
                        and row.get("trigger", {}).get("source") == SOURCE for row in inventory["automations"]),
                "More than one automation uses the dashboard source; resolve routing before running")
        fingerprint = hashlib.sha256(encode(data)).hexdigest()
        with self.lock():
            config = self.config()
            require(config and config.get("state") == "ready" and identifier(config.get("org_id")), "Connect Explore before running it")
            journal = self.root / (data["request_id"] + ".json")
            record = read_json(journal)
            if record:
                require(record.get("fingerprint") == fingerprint, "This request ID belongs to different inputs")
                require(record.get("state") == "dispatched", "This request may already have started; inspect Automation history before creating another")
                return {"kind": "dispatch", **{key: record[key] for key in ("automation_id", "request_id", "run_id")}}
            event = {"schema": "openspec-dashboard/v1", "type": "explore.requested", "stage": "explore", "approval": "explore",
                     **{key: data[key] for key in ("request_id", "workspace", "change", "request", "parameters")}}
            record = {"state": "dispatching", "fingerprint": fingerprint, "automation_id": item["id"], "request_id": data["request_id"]}
            atomic_json(journal, record)
            raw = encode(event)
            signature = "sha256=" + hmac.new(config["secret"].encode(), raw, hashlib.sha256).hexdigest()
            result = self.requester(self.base + f"/events/{config['org_id']}/{SOURCE}", method="POST", body=raw,
                                    headers={"X-Signature-256": signature})
            require(isinstance(result, dict) and result.get("received") is True and result.get("matched") == 1
                    and len(result.get("runs_created", [])) == 1 and identifier(result["runs_created"][0]),
                    "Expected exactly one Explore run; inspect Automation history before trying again")
            record.update(state="dispatched", run_id=result["runs_created"][0])
            atomic_json(journal, record)
            return {"kind": "dispatch", **{key: record[key] for key in ("automation_id", "request_id", "run_id")}}


def handle(value):
    require(isinstance(value, dict) and set(value) <= {"action", "service", "home", "input"}, "Invalid bridge request")
    require(value.get("action") in ("probe", "setup", "dispatch"), "Unsupported bridge action")
    bridge = Bridge(value.get("service"), value.get("home"))
    if value["action"] == "dispatch":
        return bridge.dispatch(value.get("input"))
    require("input" not in value, "Unexpected bridge inputs")
    return bridge.probe() if value["action"] == "probe" else bridge.setup()


if __name__ == "__main__":
    try:
        require(len(sys.argv) == 2 and len(sys.argv[1]) <= 65536, "Invalid bridge input")
        result = handle(json.loads(base64.b64decode(sys.argv[1], validate=True)))
        print(json.dumps({"version": 1, **result}, ensure_ascii=False))
    except BridgeError as error:
        print(json.dumps({"version": 1, "kind": "error", "message": str(error)}))
        sys.exit(1)
    except Exception:
        print(json.dumps({"version": 1, "kind": "error", "message": "Could not complete the local Automation request; inspect its history before retrying"}))
        sys.exit(1)
