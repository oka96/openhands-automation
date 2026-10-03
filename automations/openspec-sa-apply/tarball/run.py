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
import subprocess
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
ROLES = ("SA", "Frontend", "Backend", "QA")
ROLE_STAGES = ("propose", "update", "apply")
ROLE_CONFIG_FIELDS = {"workspace", "spec_store", "store_id", "skill_root", "profile", "timeout_seconds", "canvas_url", "mode", "stage", "role"}
ROLE_EVENT_FIELDS = {"schema", "type", "stage", "approval", "request_id", "spec_store", "requirement_id", "context_change", "role", "change", "request"}
CHANGE_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


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
    if isinstance(config, dict) and config.get("mode") == "role":
        return load_role_config(config)
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
    config["canvas_url"] = local_url(config.get("canvas_url", "http://127.0.0.1:8000"))
    return config


def load_role_config(config):
    """Read immutable deployment settings before accepting any event input."""
    if set(config) != ROLE_CONFIG_FIELDS or config.get("stage") not in ROLE_STAGES or config.get("role") not in ROLES:
        raise RunError("Invalid role automation configuration")
    config = dict(config)
    for key in ("workspace", "spec_store", "skill_root"):
        value = config[key]
        if not isinstance(value, str) or not Path(value).is_absolute() or ".local" in Path(value).parts:
            raise RunError(f"Role {key} must be an absolute directory outside .local")
        path = Path(value).resolve()
        if not path.is_dir() or ".local" in path.parts:
            raise RunError(f"Role {key} directory is unavailable")
        config[key] = str(path)
    if config["workspace"] == config["spec_store"]:
        raise RunError("Role spec store and implementation workspace must be separate")
    for key in ("workspace", "spec_store"):
        if not (Path(config[key]) / "openspec").is_dir():
            raise RunError(f"Role {key} must already contain an OpenSpec project")
    if not isinstance(config["store_id"], str) or not CHANGE_NAME.fullmatch(config["store_id"]):
        raise RunError("Role store ID must be lowercase kebab-case")
    if type(config["timeout_seconds"]) is not int or not 60 <= config["timeout_seconds"] <= 1800:
        raise RunError("Role timeout_seconds must be an integer from 60 to 1800")
    if not isinstance(config["profile"], str) or not config["profile"].strip():
        raise RunError("Role profile must be a saved agent profile name")
    config["canvas_url"] = local_url(config["canvas_url"])
    skill = Path(config["skill_root"]) / ".agents/skills" / STAGES[config["stage"]] / "SKILL.md"
    if not skill.is_file():
        raise RunError(f"Role skill root is missing {STAGES[config['stage']]}")
    return config


def require_role_trigger(env, config):
    """Role runs have no shared input defaults and never allow zero-input Run."""
    try:
        payload = json.loads(env.get("AUTOMATION_EVENT_PAYLOAD", ""))
    except (TypeError, ValueError):
        raise RunError("A signed role action event is required") from None
    stage, role = config["stage"], config["role"]
    expected_trigger = {"type": "event", "source": "openspec-role-dashboard", "on": f"{stage}.requested",
                        "filter": f"schema == 'openspec-role-dashboard/v1' && stage == '{stage}' && approval == '{stage}' && role == '{role}'"}
    defaults = {"destination": "dispatch_run", "subject_key_expr": None, "turn_text_expr": None, "wake_agent": True}
    trigger = payload.get("trigger_payload") if isinstance(payload, dict) else None
    if (not isinstance(payload, dict) or payload.get("trigger") != "event"
            or not isinstance(trigger, dict) or set(trigger) - (expected_trigger.keys() | defaults.keys())
            or any(trigger.get(key) != value for key, value in expected_trigger.items())
            or any(key in trigger and trigger[key] != value for key, value in defaults.items())):
        raise RunError("A signed role action event is required")
    event = payload.get("event")
    # CustomWebhookEvent.model_dump() is the native dispatch shape. The signed
    # request is nested in payload; validate routing metadata before unwrapping.
    if isinstance(event, dict) and "payload" in event:
        if (set(event) != {"payload", "source_override", "event_key"}
                or event["source_override"] != "openspec-role-dashboard"
                or event["event_key"] != f"{stage}.requested"):
            raise RunError("Invalid native role event wrapper; source and event key must match this action")
        event = event["payload"]
    if (not isinstance(event, dict) or set(event) != ROLE_EVENT_FIELDS
            or event.get("schema") != "openspec-role-dashboard/v1"
            or event.get("stage") != stage or event.get("approval") != stage
            or event.get("type") != f"{stage}.requested" or event.get("role") != role):
        raise RunError("Invalid role action event; submit an explicit role and stage")
    if event["spec_store"] != config["spec_store"]:
        raise RunError("Role event spec store must match this automation's configured store")
    for key in ("change", "context_change"):
        if not isinstance(event[key], str) or len(event[key]) > 100 or not CHANGE_NAME.fullmatch(event[key]):
            raise RunError(f"Role {key} must be a kebab-case name of at most 100 characters")
    if not isinstance(event["requirement_id"], str) or not re.fullmatch(r"REQ-[0-9]+", event["requirement_id"]):
        raise RunError("Invalid role requirement ID")
    if (not isinstance(event["request"], str) or len(event["request"]) > 10000
            or (stage in ("propose", "update") and not event["request"].strip())):
        raise RunError("Role Propose and Update require a prompt; prompts must be at most 10000 characters")
    if ((stage == "propose" and event["change"] == event["context_change"])
            or (stage != "propose" and event["change"] != event["context_change"])):
        raise RunError("Propose requires a distinct new change; Update and Apply must use the context change")
    try:
        if str(uuid.UUID(event["request_id"])) != event["request_id"]:
            raise ValueError()
    except (TypeError, ValueError, AttributeError):
        raise RunError("Invalid role request ID") from None
    return event


def role_cli(config, *arguments):
    """Use only the project's installed CLI; never download or invoke a shell."""
    try:
        completed = subprocess.run(["npx", "--no-install", "openspec", *arguments],
                                   cwd=config["workspace"], capture_output=True, timeout=20, check=False)
        if completed.returncode or len(completed.stdout) > 1_000_000:
            raise RunError("Pinned OpenSpec CLI check failed; inspect the selected store and change")
        value = json.loads(completed.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        raise RunError("Pinned OpenSpec CLI is unavailable or returned invalid data") from None
    if not isinstance(value, dict):
        raise RunError("Pinned OpenSpec CLI returned an invalid object")
    return value


def safe_store_file(config, path):
    root = Path(config["spec_store"])
    path = Path(path)
    try:
        relative = path.relative_to(root)
    except ValueError:
        raise RunError("Role artifact path is outside the configured spec store") from None
    if ".local" in relative.parts or any((root.joinpath(*relative.parts[:n])).is_symlink()
                                       for n in range(1, len(relative.parts) + 1)):
        raise RunError("Role artifacts must not use symlinks or .local paths")
    return path


def read_role_metadata(config):
    path = safe_store_file(config, Path(config["spec_store"]) / "openspec/requirements.json")
    try:
        if path.stat().st_size > 128 * 1024:
            raise RunError("Requirement metadata exceeds 128 KiB")
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise RunError("Cannot read valid requirement metadata from the configured store") from None
    if (not isinstance(metadata, dict) or metadata.get("version") != 1
            or not isinstance(metadata.get("requirements"), list) or not 1 <= len(metadata["requirements"]) <= 50):
        raise RunError("Requirement metadata must contain 1 to 50 requirements")
    ids, changes = set(), set()
    for item in metadata["requirements"]:
        if (not isinstance(item, dict) or not isinstance(item.get("id"), str)
                or not re.fullmatch(r"REQ-[0-9]+", item["id"])
                or not isinstance(item.get("change"), str) or not CHANGE_NAME.fullmatch(item["change"])
                or not isinstance(item.get("roles"), dict) or set(item["roles"]) != set(ROLES)
                or item["id"] in ids or item["change"] in changes):
            raise RunError("Requirement metadata has invalid, duplicate, or missing role associations")
        ids.add(item["id"])
        changes.add(item["change"])
    return metadata


def validate_role_store(config):
    stores = role_cli(config, "store", "list", "--json").get("stores", [])
    matches = [item for item in stores if isinstance(item, dict) and item.get("id") == config["store_id"]]
    if (len(matches) != 1 or not isinstance(matches[0].get("root"), str)
            or str(Path(matches[0]["root"]).resolve()) != config["spec_store"]):
        raise RunError("Registered OpenSpec store ID does not match the configured spec store")


def role_tasks(config, *, require_ready=True):
    expected_path = Path(config["spec_store"]) / "openspec/changes" / config["change"] / "tasks.md"
    safe_store_file(config, expected_path)
    data = role_cli(config, "instructions", "apply", "--change", config["change"],
                    "--store", config["store_id"], "--json")
    if require_ready and data.get("state") not in ("ready", "all_done"):
        raise RunError("The selected store change has incomplete or blocked planning artifacts")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks or len(tasks) > 500:
        raise RunError("The selected store change must have 1 to 500 tagged tasks")
    seen = set()
    for task in tasks:
        if (not isinstance(task, dict) or not isinstance(task.get("description"), str)
                or type(task.get("done")) is not bool or task.get("sourcePath") != str(expected_path)
                or type(task.get("line")) is not int or task["line"] <= 0):
            raise RunError("OpenSpec returned invalid task sources")
        tags = re.findall(r"\[(SA|Frontend|Backend|QA)\]", task["description"])
        if len(tags) != 1 or task["description"] in seen:
            raise RunError("Every task needs one role tag and a unique description")
        task["role"] = tags[0]
        seen.add(task["description"])
    if {task["role"] for task in tasks} != set(ROLES):
        raise RunError("The requirement must have nonempty SA, Frontend, Backend, and QA task sets")
    return tasks


def role_preflight(config, event):
    """Validate effective event inputs and current associations under both locks."""
    config = {**config, **{key: event[key] for key in ("change", "context_change", "requirement_id", "request")},
              "dashboard_request_id": event["request_id"], "skill": STAGES[config["stage"]]}
    validate_role_store(config)
    metadata = read_role_metadata(config)
    matches = [item for item in metadata["requirements"] if item["id"] == config["requirement_id"]]
    if len(matches) != 1 or matches[0]["change"] != config["context_change"]:
        raise RunError("The requirement/context change association has changed; refresh the board")
    context = safe_store_file(config, Path(config["spec_store"]) / "openspec/changes" / config["context_change"])
    target = safe_store_file(config, Path(config["spec_store"]) / "openspec/changes" / config["change"])
    if not context.is_dir():
        raise RunError("The context requirement's active change is missing")
    for entry in context.rglob("*"):
        safe_store_file(config, entry)
    if config["stage"] == "propose":
        if target.exists() or any(item["change"] == config["change"] for item in metadata["requirements"]):
            raise RunError("The proposed change already exists; choose a new unused change name")
        if len(metadata["requirements"]) >= 50:
            raise RunError("The board's 50 requirement limit has been reached")
    else:
        if not target.is_dir():
            raise RunError("The selected active store change does not exist")
        config["selected_tasks"] = [task for task in role_tasks(config, require_ready=config["stage"] == "apply") if task["role"] == config["role"]]
    return config, metadata


def scope_snapshot(root):
    """Audit project content without reading credentials, Git internals, or dependencies."""
    root = Path(root)
    snapshot = {}
    excluded = {".git", ".local", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in excluded)
        for name in list(dirs):
            path = Path(directory) / name
            if path.is_symlink():
                snapshot[str(path.relative_to(root))] = "symlink:" + os.readlink(path)
                dirs.remove(name)
        for name in sorted(files):
            path = Path(directory) / name
            relative = str(path.relative_to(root))
            if path.is_symlink():
                snapshot[relative] = "symlink:" + os.readlink(path)
            else:
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(65536), b""):
                        digest.update(chunk)
                snapshot[relative] = digest.hexdigest()
            if len(snapshot) > 25000:
                raise RunError("Project scope audit exceeds 25000 files")
    return snapshot


def changed_paths(before, after):
    return {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}


def audit_role_scope(config, before_store, before_workspace, before_tasks, result):
    changed = changed_paths(before_store, scope_snapshot(config["spec_store"]))
    prefix = f"openspec/changes/{config['change']}/"
    allowed = lambda path: path == prefix + "tasks.md" if config["stage"] == "apply" else path.startswith(prefix)
    if any(not allowed(path) for path in changed):
        raise RunError("Role action changed files outside its permitted store scope; inspect the conversation and preserve recovery evidence")
    for entry in (Path(config["spec_store"]) / prefix).rglob("*"):
        safe_store_file(config, entry)
    if config["stage"] != "apply" and scope_snapshot(config["workspace"]) != before_workspace:
        raise RunError("Planning action changed implementation files; inspect the conversation before continuing")
    if config["stage"] == "apply":
        path = safe_store_file(config, Path(config["spec_store"]) / prefix / "tasks.md")
        after = path.read_text(encoding="utf-8")
        old_lines, new_lines = before_tasks.splitlines(keepends=True), after.splitlines(keepends=True)
        if len(old_lines) != len(new_lines):
            raise RunError("Apply may change selected role checkboxes only, not task structure")
        newly_done = set()
        selected_lines = {task["line"]: task for task in config["selected_tasks"]}
        for number, (old, new) in enumerate(zip(old_lines, new_lines), start=1):
            if old == new:
                continue
            task = selected_lines.get(number)
            pattern = r"^(\s*[-*+]\s+\[)(\s*\S?\s*)(\].*)$"
            a, b = re.match(pattern, old.rstrip("\r\n")), re.match(pattern, new.rstrip("\r\n"))
            if (not task or not a or not b or a.group(1, 3) != b.group(1, 3)
                    or old[len(old.rstrip("\r\n")):] != new[len(new.rstrip("\r\n")):]
                    or b.group(2).strip().lower() != "x"):
                raise RunError("Apply changed task text or another role's task; only selected role completion is allowed")
            if not task["done"]:
                newly_done.add(task["description"])
        evidence = result.get("task_evidence", [])
        if not isinstance(evidence, list):
            raise RunError("Apply task evidence must be an array")
        evidenced = {entry["task"] for entry in evidence if isinstance(entry, dict)
                     and isinstance(entry.get("task"), str) and isinstance(entry.get("evidence"), str)
                     and entry["evidence"].strip()}
        if newly_done - evidenced:
            raise RunError("Apply checked tasks without concrete task_evidence in its final result")


def validate_role_result(config, metadata, before_tasks, result):
    if result["status"] != "completed":
        return result
    report = role_cli(config, "validate", config["change"], "--store", config["store_id"],
                      "--strict", "--json", "--no-interactive")
    items = report.get("items", [])
    if len(items) != 1 or items[0].get("id") != config["change"] or items[0].get("valid") is not True:
        raise RunError("The role action did not produce a strictly valid OpenSpec change")
    status = role_cli(config, "status", "--change", config["change"], "--store", config["store_id"], "--json")
    if status.get("isPlanningComplete") is not True:
        raise RunError("The role action left incomplete planning artifacts")
    tasks = role_tasks(config)
    if config["stage"] == "apply" and any(not task["done"] for task in tasks if task["role"] == config["role"]):
        raise RunError("Apply reported completed while selected role tasks remain unfinished")
    if config["stage"] == "update":
        old_done = {match.group(1) for match in re.finditer(r"^\s*[-*+]\s+\[\s*[xX]\s*\]\s+(.+?)\s*$", before_tasks, re.M)}
        if any(task["done"] and task["description"] not in old_done for task in tasks):
            raise RunError("Update must not newly complete tasks or transfer completion to revised task text")
    if config["stage"] == "propose":
        if any(task["done"] for task in tasks):
            raise RunError("A new proposal must start with all role tasks unchecked")
        current = read_role_metadata(config)
        if current != metadata:
            raise RunError("Requirement metadata changed during Propose; review it before registering the new requirement")
        number = max(int(item["id"].split("-")[1]) for item in metadata["requirements"]) + 1
        requirement_id = f"REQ-{number:03d}"
        text = " ".join(config["request"].split())
        current["requirements"].append({"id": requirement_id, "title": text[:160], "summary": text[:500],
                                        "change": config["change"],
                                        "roles": {role: {"owner": "Unassigned", "state": "backlog", "note": ""} for role in ROLES}})
        path = safe_store_file(config, Path(config["spec_store"]) / "openspec/requirements.json")
        content = (json.dumps(current, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        if len(content) > 128 * 1024:
            raise RunError("New requirement metadata would exceed the board size limit")
        descriptor, temporary = tempfile.mkstemp(prefix=".requirements-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        result = {**result, "requirement_id": requirement_id,
                  "summary": f"Registered {requirement_id} ({config['change']}) with all four roles. " + result["summary"]}
    return result


def run_role(client, config, event, prompt, env):
    deadline = time.monotonic() + config["timeout_seconds"]
    # Deterministic order prevents two role runs that share either root deadlocking.
    with contextlib.ExitStack() as stack:
        for path in sorted({config["workspace"], config["spec_store"]}):
            stack.enter_context(workspace_lock(path))
        config, metadata = role_preflight(config, event)
        claim_dashboard_request(event, Path.home() / ".openhands/apps/openspec-progress/role-consumed")
        before_store = scope_snapshot(config["spec_store"])
        before_workspace = scope_snapshot(config["workspace"]) if config["stage"] != "apply" else None
        task_path = Path(config["spec_store"]) / "openspec/changes" / config["change"] / "tasks.md"
        before_tasks = task_path.read_text(encoding="utf-8") if config["stage"] != "propose" else ""
        prompt += "\n\nRun configuration (data for this explicitly selected role action):\n" + json.dumps(config, indent=2)
        # Role profile selection is fixed by configuration, not injected per-run overrides.
        result = client.run(config, prompt, run_id=env.get("AUTOMATION_RUN_ID", ""), deadline=deadline)
        audit_role_scope(config, before_store, before_workspace, before_tasks, result)
        return validate_role_result(config, metadata, before_tasks, result)


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

    def run(self, config, prompt, *, profile_id=None, run_id="", deadline=None):
        # Role postflight performs three bounded CLI checks before its callback.
        reserve = min(90, config["timeout_seconds"] // 2) if config.get("mode") == "role" else 30
        deadline = (self.clock() + config["timeout_seconds"] if deadline is None else deadline) - reserve
        if not profile_id:
            profiles = self.request("/api/agent-profiles", deadline=deadline)
            matches = [p for p in profiles.get("profiles", [])
                       if p.get("name") == config["profile"] and p.get("id")]
            if len(matches) != 1:
                raise RunError("Saved agent profile is unavailable or ambiguous")
            profile_id = matches[0]["id"]
        settings = self.request("/api/settings", deadline=deadline)
        options = conversation_options(settings.get("conversation_settings", {}))
        tags = {"openspecstage": config["stage"], "openspecskill": STAGES[config["stage"]],
                "openspecchange": config["change"], "automationrunid": run_id,
                "automationtrigger": "automation"}
        role_run = config.get("mode") == "role"
        if role_run:
            tags.update(requirement=config["requirement_id"], role=config["role"])
        message = {"role": "user", "content": [{"type": "text", "text": prompt}], "run": True}
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
                "initial_message": None if role_run else message,
                "tags": tags,
            })
            if created.get("id") != self.conversation_id:
                raise RunError("OpenHands returned an unexpected conversation ID")
            if role_run:
                # Creation runs any initial message; send it only after naming succeeds.
                named = self.request(path, method="PATCH", deadline=deadline,
                                     body={"title": f"[{config['role']}] {config['change']}"})
                if named.get("success") is not True:
                    raise RunError("OpenHands could not save the role conversation title")
                started = self.request(path + "/events", method="POST", deadline=deadline, body=message)
                if started.get("success") is not True:
                    raise RunError("OpenHands could not start the named role conversation")
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
            fields = ("stage", "workspace", "profile", "spec_store", "store_id") if config.get("mode") == "role" else ("stage", "workspace", "change", "profile")
            if config.get("mode") == "role":
                validate_role_store(config)
                read_role_metadata(config)
            print(json.dumps({"status": "valid", **{k: config[k] for k in fields}}))
            return 0
        # Validate callback configuration before creating a conversation.
        if not env.get("AUTOMATION_CALLBACK_URL") or not env.get("AUTOMATION_CALLBACK_API_KEY") or not env.get("AUTOMATION_RUN_ID"):
            raise RunError("Automation callback environment is incomplete")
        local_url(env["AUTOMATION_CALLBACK_URL"], origin_only=False)
        role_run = config.get("mode") == "role"
        dashboard_input = require_role_trigger(env, config) if role_run else require_manual_trigger(env, config)
        origin = env.get("AGENT_SERVER_URL")
        key = env.get("SESSION_API_KEY") or env.get("OH_SESSION_API_KEYS_0")
        if not origin or not key:
            raise RunError("AGENT_SERVER_URL and an injected session key are required")
        client = Client(origin, key)
        if role_run:
            result = run_role(client, config, dashboard_input, prompt, env)
        else:
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
