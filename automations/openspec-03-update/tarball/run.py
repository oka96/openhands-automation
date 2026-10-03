#!/usr/bin/env python3
"""Run one approved OpenSpec stage on the local OpenHands Agent Server."""

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


STAGES = {
    "explore": "openspec-explore",
    "propose": "openspec-propose",
    "update": "openspec-update-change",
    "apply": "openspec-apply-change",
    "verify": "openspec-apply-change",
    "sync": "openspec-sync-specs",
    "archive": "openspec-archive-change",
}
ANALYZERS = {
    "llm": "LLMSecurityAnalyzer",
    "pattern": "PatternSecurityAnalyzer",
    "policy_rail": "PolicyRailSecurityAnalyzer",
}


class RunError(Exception):
    """An actionable, safe-to-log automation failure."""


def local_url(value, *, origin_only=True):
    """Restrict authenticated requests to the local deployment; never redirect."""
    try:
        parsed = urllib.parse.urlsplit(value)
        parsed.port  # Reject malformed port numbers too.
    except (TypeError, ValueError):
        raise RunError("URL must refer to a loopback HTTP(S) server") from None
    if (parsed.scheme not in ("http", "https")
            or parsed.hostname not in ("localhost", "127.0.0.1", "::1")
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or (origin_only and parsed.path not in ("", "/"))):
        raise RunError("URL must refer to a loopback HTTP(S) server")
    return value.rstrip("/") if origin_only else value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, *, method="GET", body=None, headers=None, timeout=10):
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url, data=payload, method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=timeout) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise RunError("OpenHands response exceeded the size limit")
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        code = error.code
        error.close()
        if code in (401, 403):
            raise RunError("OpenHands authentication failed; check the injected session or callback key") from None
        raise RunError(f"OpenHands request returned HTTP {code}") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RunError("OpenHands request failed or timed out") from None
    except (ValueError, UnicodeError):
        raise RunError("OpenHands returned invalid JSON") from None


def conversation_options(settings):
    if not isinstance(settings, dict):
        raise RunError("OpenHands conversation settings must be an object")
    analyzer = settings.get("security_analyzer")
    security = None
    if isinstance(analyzer, str):
        if analyzer in ANALYZERS:
            security = {"kind": ANALYZERS[analyzer]}
        elif analyzer not in ("", "none"):
            raise RunError("Unsupported OpenHands security analyzer setting")
    elif analyzer is not None:
        if not isinstance(analyzer, dict) or analyzer.get("kind") not in ANALYZERS.values():
            raise RunError("Unsupported OpenHands security analyzer configuration")
        security = analyzer
    policy = settings.get("confirmation_policy")
    if policy is None:
        policy = {"kind": "NeverConfirm"}
        if settings.get("confirmation_mode") is True:
            policy = ({"kind": "ConfirmRisky", "threshold": "HIGH", "confirm_unknown": True}
                      if security and security["kind"] == "LLMSecurityAnalyzer"
                      else {"kind": "AlwaysConfirm"})
    if not isinstance(policy, dict) or policy.get("kind") not in ("NeverConfirm", "AlwaysConfirm", "ConfirmRisky"):
        raise RunError("Unsupported OpenHands confirmation policy")
    options = {"confirmation_policy": policy}
    if security is not None:
        options["security_analyzer"] = security
    return options


def load_config(path):
    try:
        config = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        raise RunError("Cannot read a valid config.json") from None
    if not isinstance(config, dict) or config.get("stage") not in STAGES:
        raise RunError("config.json must specify a supported OpenSpec stage")
    if not isinstance(config.get("change"), str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", config["change"]):
        raise RunError("Change must be a lowercase kebab-case name")
    workspace = config.get("workspace")
    if not isinstance(workspace, str) or not Path(workspace).is_absolute():
        raise RunError("Workspace must be an absolute local directory")
    workspace = Path(workspace).resolve()
    if not workspace.is_dir() or not (workspace / "openspec").is_dir():
        raise RunError("Workspace must already contain an OpenSpec project")
    config["workspace"] = str(workspace)
    skill = workspace / ".agents" / "skills" / STAGES[config["stage"]] / "SKILL.md"
    if not skill.is_file():
        raise RunError(f"Workspace is missing the {STAGES[config['stage']]} skill")
    request = config.get("request", "")
    if not isinstance(request, str):
        raise RunError("Request must be text")
    if config["stage"] in ("propose", "update") and not request.strip():
        raise RunError("Set a concrete request in config.json before running propose or update")
    config["request"] = request
    change = workspace / "openspec" / "changes" / config["change"]
    if config["stage"] in ("apply", "update", "verify", "sync", "archive") and not change.is_dir():
        raise RunError("The selected active OpenSpec change does not exist")
    if config["stage"] == "propose" and change.exists():
        raise RunError("The proposed change already exists; use update or choose a new name")
    timeout = config.get("timeout_seconds", 1800)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 60 <= timeout <= 1800:
        raise RunError("timeout_seconds must be an integer between 60 and 1800")
    config["timeout_seconds"] = timeout
    profile = config.get("profile", "codex-acp-demo")
    if not isinstance(profile, str) or not profile.strip():
        raise RunError("Profile must be a saved agent profile name")
    config["profile"] = profile
    config["canvas_url"] = local_url(config.get("canvas_url", "http://127.0.0.1:8002"))
    return config


def require_manual_trigger(env, config=None):
    """Allow manual Run or a validated, explicit dashboard Explore request."""
    try:
        payload = json.loads(env.get("AUTOMATION_EVENT_PAYLOAD", ""))
    except (TypeError, ValueError):
        raise RunError("A valid manual OpenSpec automation trigger is required") from None
    if not isinstance(payload, dict):
        raise RunError("A valid manual OpenSpec automation trigger is required")
    trigger = payload.get("trigger_payload")
    dashboard_filter = "schema == 'openspec-dashboard/v1' && stage == 'explore' && approval == 'explore'"
    if (isinstance(trigger, dict) and trigger.get("source") == "openspec-dashboard"
            and payload.get("trigger") == "event" and trigger.get("type") == "event"
            and trigger.get("on") == "explore.requested" and trigger.get("filter") == dashboard_filter):
        if not config or config.get("stage") != "explore":
            raise RunError("Dashboard inputs are supported only by the Explore automation")
        if "event" not in payload:
            return None  # Native manual Run still uses the configured defaults.
        event = payload["event"]
        fields = {"schema", "type", "stage", "approval", "request_id", "workspace", "change", "request", "parameters"}
        if (not isinstance(event, dict) or set(event) != fields
                or event.get("schema") != "openspec-dashboard/v1"
                or event.get("type") != "explore.requested"
                or event.get("stage") != "explore" or event.get("approval") != "explore"):
            raise RunError("Invalid dashboard Explore request")
        if (not isinstance(event["workspace"], str) or not Path(event["workspace"]).is_absolute()
                or str(Path(event["workspace"]).resolve()) != config["workspace"]):
            raise RunError("Dashboard workspace must match this automation's configured workspace")
        if (not isinstance(event["change"], str) or len(event["change"]) > 100
                or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", event["change"])):
            raise RunError("Dashboard change must be a kebab-case name of at most 100 characters")
        if not isinstance(event["request"], str) or not event["request"].strip() or len(event["request"]) > 10000:
            raise RunError("Dashboard prompt must contain 1 to 10000 characters")
        try:
            parameters_size = len(json.dumps(event["parameters"], ensure_ascii=False, allow_nan=False,
                                            separators=(",", ":")).encode())
        except (TypeError, ValueError):
            raise RunError("Dashboard parameters must be valid JSON") from None
        if not isinstance(event["parameters"], dict) or parameters_size > 8192:
            raise RunError("Dashboard parameters must be a JSON object of at most 8 KiB")
        try:
            if str(uuid.UUID(event["request_id"])) != event["request_id"]:
                raise ValueError()
        except (TypeError, ValueError, AttributeError):
            raise RunError("Invalid dashboard request ID") from None
        return event
    if (payload.get("trigger") != "event" or "event" in payload
            or not isinstance(trigger, dict) or trigger.get("type") != "event"
            or trigger.get("source") != "openspec-manual" or trigger.get("on") != "manual-only"
            or trigger.get("filter") != "`false`"):
        raise RunError("This OpenSpec stage must be started manually from its Run action")


def claim_dashboard_request(event, directory=None):
    """A replay can create another native run, but must never start another agent."""
    root = directory or Path.home() / ".openhands/apps/openspec-progress/consumed"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(root / event["request_id"], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
    except FileExistsError:
        raise RunError("This dashboard request was already consumed; inspect its original run") from None


def terminal_result(response):
    if not isinstance(response, str):
        raise RunError("Agent did not return the required terminal JSON result")
    # ACP can flatten commentary and final into one response. Only accept a
    # result at the very end; an earlier success followed by prose is not final.
    response = response.strip()
    fenced = re.search(r"```(?:json)?[ \t]*\n([\s\S]*?)\n```\s*$", response)
    source = fenced.group(1).strip() if fenced else response
    candidates = [source]
    for match in re.finditer(r'\{\s*"(?:status|summary|findings)"\s*:', source):
        candidates.insert(0, source[match.start():])
    result = None
    for candidate in candidates:
        try:
            result = json.loads(candidate)
            break
        except ValueError:
            continue
    if result is None:
        raise RunError("Agent did not return the required terminal JSON result")
    if (not isinstance(result, dict)
            or result.get("status") not in ("completed", "blocked", "findings")
            or not isinstance(result.get("summary"), str) or not result["summary"].strip()
            or not isinstance(result.get("findings"), list)
            or any(not isinstance(item, (str, dict)) for item in result["findings"])):
        raise RunError("Agent terminal JSON has an invalid result schema")
    if result["status"] == "completed" and result["findings"]:
        raise RunError("Agent reported completion with unresolved findings")
    return result


@contextlib.contextmanager
def workspace_lock(workspace):
    digest = hashlib.sha256(workspace.encode()).hexdigest()
    path = Path(tempfile.gettempdir()) / f"openhands-openspec-{digest}.lock"
    with path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RunError("Another OpenSpec automation is already using this workspace") from None
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


class Client:
    def __init__(self, origin, key, *, requester=request_json, clock=time.monotonic, sleep=time.sleep):
        self.origin = local_url(origin)
        self.key = key
        self.requester = requester
        self.clock = clock
        self.sleep = sleep
        self.conversation_id = None

    def request(self, path, *, method="GET", body=None, deadline=None):
        timeout = 10 if deadline is None else min(10, deadline - self.clock())
        if timeout <= 0:
            raise RunError("OpenSpec stage timed out")
        return self.requester(self.origin + path, method=method, body=body,
                              headers={"X-Session-API-Key": self.key}, timeout=timeout)

    def run(self, config, prompt, *, profile_id=None, run_id=""):
        deadline = self.clock() + config["timeout_seconds"] - 30
        if not profile_id:
            profiles = self.request("/api/agent-profiles", deadline=deadline)
            matches = [p for p in profiles.get("profiles", [])
                       if p.get("name") == config["profile"] and p.get("id")]
            if len(matches) != 1:
                raise RunError("Saved agent profile is unavailable or ambiguous")
            profile_id = matches[0]["id"]
        settings = self.request("/api/settings", deadline=deadline)
        options = conversation_options(settings.get("conversation_settings", {}))
        self.conversation_id = str(uuid.uuid4())
        path = f"/api/conversations/{self.conversation_id}"
        print(json.dumps({"conversation_id": self.conversation_id,
                          "url": f"{config['canvas_url']}/conversations/{self.conversation_id}?backend=default-local"}), flush=True)
        try:
            created = self.request("/api/conversations", method="POST", deadline=deadline, body={
                "conversation_id": self.conversation_id,
                "agent_profile_id": profile_id,
                "workspace": {"kind": "LocalWorkspace", "working_dir": config["workspace"]},
                "worktree": False, "autotitle": False, "stuck_detection": True,
                "max_iterations": 100, **options,
                "initial_message": {"role": "user", "content": [{"type": "text", "text": prompt}], "run": True},
                "tags": {"openspecstage": config["stage"], "openspecchange": config["change"],
                         "automationrunid": run_id, "automationtrigger": "automation"},
            })
            if created.get("id") != self.conversation_id:
                raise RunError("OpenHands returned an unexpected conversation ID")
            while True:
                state = self.request(path, deadline=deadline)
                status = state.get("execution_status")
                if status in ("error", "stuck", "paused", "waiting_for_confirmation"):
                    raise RunError(f"Conversation requires attention: {status}")
                if status not in ("idle", "running", "finished"):
                    raise RunError("OpenHands returned an unknown conversation status")
                if status == "finished":
                    final = self.request(path + "/agent_final_response", deadline=deadline)
                    if final.get("response"):
                        return terminal_result(final["response"])
                remaining = deadline - self.clock()
                if remaining <= 0:
                    raise RunError("OpenSpec stage timed out")
                self.sleep(min(1, remaining))
        except BaseException:
            try:
                self.request(path + "/pause", method="POST")
            except Exception:
                print("Could not confirm conversation pause; inspect the linked conversation before starting another run", flush=True)
            raise


def fire_callback(result, env, *, conversation_id=None, requester=request_json):
    url = env.get("AUTOMATION_CALLBACK_URL")
    if not url:
        raise RunError("AUTOMATION_CALLBACK_URL is missing")
    local_url(url, origin_only=False)
    status = "COMPLETED" if result["status"] == "completed" else "FAILED"
    body = {"status": status, "run_id": env.get("AUTOMATION_RUN_ID", "")}
    if conversation_id:
        body["conversation_id"] = conversation_id
    if status == "FAILED":
        body["error"] = result["summary"]
    requester(url, method="POST", body=body, timeout=10,
              headers={"Authorization": "Bearer " + env.get("AUTOMATION_CALLBACK_API_KEY", "")})


def redact(text, env):
    for name in ("SESSION_API_KEY", "OH_SESSION_API_KEYS_0", "AUTOMATION_CALLBACK_API_KEY"):
        if env.get(name):
            text = text.replace(env[name], "[redacted]")
    return text


def main(argv=None, *, env=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    parser.add_argument("--prompt", type=Path, default=Path(__file__).with_name("prompt.md"))
    parser.add_argument("--check", action="store_true", help="Validate local prerequisites without starting a conversation")
    args = parser.parse_args(argv)
    env = dict(os.environ if env is None else env)
    client = None
    result = None
    old_handlers = {}

    def interrupted(signum, frame):
        raise RunError("OpenSpec stage interrupted")

    try:
        for signum in (signal.SIGTERM, signal.SIGINT):
            old_handlers[signum] = signal.signal(signum, interrupted)
        config = load_config(args.config)
        try:
            prompt = args.prompt.read_text()
        except OSError:
            raise RunError("Cannot read prompt.md") from None
        if not prompt.strip():
            raise RunError("prompt.md is empty")
        if args.check:
            print(json.dumps({"status": "valid", **{k: config[k] for k in ("stage", "workspace", "change", "profile")}}))
            return 0
        # Validate callback configuration before creating a conversation.
        if not env.get("AUTOMATION_CALLBACK_URL") or not env.get("AUTOMATION_CALLBACK_API_KEY") or not env.get("AUTOMATION_RUN_ID"):
            raise RunError("Automation callback environment is incomplete")
        local_url(env["AUTOMATION_CALLBACK_URL"], origin_only=False)
        dashboard_input = require_manual_trigger(env, config)
        origin = env.get("AGENT_SERVER_URL")
        key = env.get("SESSION_API_KEY") or env.get("OH_SESSION_API_KEYS_0")
        if not origin or not key:
            raise RunError("AGENT_SERVER_URL and an injected session key are required")
        client = Client(origin, key)
        with workspace_lock(config["workspace"]):
            # Recheck mutable prerequisites after acquiring the lock.
            config = load_config(args.config)
            dashboard_input = require_manual_trigger(env, config)
            if dashboard_input:
                claim_dashboard_request(dashboard_input)
                config.update({key: dashboard_input[key] for key in ("change", "request", "parameters")})
                config["dashboard_request_id"] = dashboard_input["request_id"]
            prompt += "\n\nRun configuration (data for this selected stage):\n" + json.dumps(config, indent=2)
            result = client.run(config, prompt, profile_id=env.get("AUTOMATION_AGENT_PROFILE_ID"),
                                run_id=env.get("AUTOMATION_RUN_ID", ""))
    except (RunError, KeyboardInterrupt) as error:
        result = {"status": "blocked", "summary": str(error) or "OpenSpec stage interrupted", "findings": []}
    except Exception:
        # Arbitrary HTTP bodies, settings, and exception reprs can contain secrets.
        result = {"status": "blocked", "summary": "Unexpected runner failure; inspect the local runner and conversation", "findings": []}
    finally:
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)
    if result is None:
        return 1
    result = json.loads(redact(json.dumps(result), env))
    print(json.dumps(result), flush=True)
    if not args.check:
        try:
            fire_callback(result, env, conversation_id=client.conversation_id if client else None)
        except RunError as error:
            print(redact(f"Completion callback failed: {error}", env), flush=True)
            return 1
        except Exception:
            print("Completion callback failed unexpectedly", flush=True)
            return 1
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
