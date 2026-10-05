#!/usr/bin/env python3
"""Run one approved OpenSpec stage on the local OpenHands Agent Server."""

import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import shutil
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
ACTION_DEFINITIONS = json.loads(Path(__file__).with_name("actions.json").read_text())
ROLE_STAGES = tuple(action["id"] for action in ACTION_DEFINITIONS)
ROLE_SKILLS = {action["id"]: action["skill"] for action in ACTION_DEFINITIONS}
_delivery_spec = importlib.util.spec_from_file_location("role_delivery", Path(__file__).with_name("delivery.py"))
delivery = importlib.util.module_from_spec(_delivery_spec)
_delivery_spec.loader.exec_module(delivery)
ROLE_CONFIG_FIELDS = {"workspace", "spec_store", "store_id", "skill_root", "profile", "timeout_seconds", "canvas_url", "mode", "stage", "role"}
ROLE_EVENT_FIELDS = {"schema", "type", "stage", "approval", "request_id", "spec_store", "requirement_id", "context_change", "role", "spec_id", "change", "request"}
CHANGE_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
ROLE_PREFIXES = {"SA": "SA", "Frontend": "FE", "Backend": "BE", "QA": "QA"}
ROLE_CHANGE = re.compile(r"(SA|FE|BE|QA)-([A-Z][A-Z0-9]*)-([0-9]+)-([a-z0-9]+(?:-[a-z0-9]+)*)")
TASK_LINE = re.compile(r"^\s*(?:[-*+]|\d{1,9}[.)])\s*\[(?:\s*([^\]\s]?)\s*\](?![([])|\s+\])\s*(.*)")


def role_change(value):
    match = ROLE_CHANGE.fullmatch(value) if isinstance(value, str) and len(value) <= 160 else None
    if not match:
        return None
    return {"role": next(role for role, prefix in ROLE_PREFIXES.items() if prefix == match[1]),
            "requirement_id": f"{match[2]}-{match[3]}", "feature": match[4]}


def valid_spec_id(value, requirement_id, role):
    identity = role_change(value)
    return bool(identity and identity["requirement_id"] == requirement_id and identity["role"] == role)


class RunError(Exception):
    """An actionable, safe-to-log automation failure."""

    def __init__(self, message, *, outcome="execution_error"):
        super().__init__(message)
        self.outcome = outcome


ROLE_LAUNCH_HELP = ("A signed role action event is required. Follow the role link from OpenSpec Kanban "
                    "or open the matching role workflow. Choose a requirement, Role spec and Automation, then submit "
                    "in that role workflow. Native Run now has no requirement context.")


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
        raise RunError(f"Workspace is missing the {STAGES[config['stage']]} automation source")
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
        if (key != "workspace" and not path.is_dir()) or ".local" in path.parts or path != Path(value):
            raise RunError(f"Role {key} directory is unavailable")
        config[key] = str(path)
    if Path(config["workspace"]) == Path(config["spec_store"]) or Path(config["workspace"]) in Path(config["spec_store"]).parents or Path(config["spec_store"]) in Path(config["workspace"]).parents:
        raise RunError("Role spec store and managed workspace parent must be separate non-overlapping directories")
    for key in ("spec_store",):
        if not (Path(config[key]) / "openspec").is_dir():
            raise RunError(f"Role {key} must already contain an OpenSpec project")
    if not isinstance(config["store_id"], str) or not CHANGE_NAME.fullmatch(config["store_id"]):
        raise RunError("Role store ID must be lowercase kebab-case")
    if type(config["timeout_seconds"]) is not int or not 60 <= config["timeout_seconds"] <= 1800:
        raise RunError("Role timeout_seconds must be an integer from 60 to 1800")
    if not isinstance(config["profile"], str) or not config["profile"].strip():
        raise RunError("Role profile must be a saved agent profile name")
    config["canvas_url"] = local_url(config["canvas_url"])
    skill_name = ROLE_SKILLS[config["stage"]]
    if skill_name and not (Path(config["skill_root"]) / ".agents/skills" / skill_name / "SKILL.md").is_file():
        raise RunError(f"Automation source directory is missing {skill_name}")
    return config


def require_role_trigger(env, config):
    """Role runs have no shared input defaults and never allow zero-input Run."""
    try:
        payload = json.loads(env.get("AUTOMATION_EVENT_PAYLOAD", ""))
    except (TypeError, ValueError):
        raise RunError(ROLE_LAUNCH_HELP, outcome="needs_review") from None
    stage, role = config["stage"], config["role"]
    expected_trigger = {"type": "event", "source": "openspec-role-dashboard", "on": f"{stage}.requested",
                        "filter": f"schema == 'openspec-role-dashboard/v3' && stage == '{stage}' && approval == '{stage}' && role == '{role}'"}
    defaults = {"destination": "dispatch_run", "subject_key_expr": None, "turn_text_expr": None, "wake_agent": True}
    trigger = payload.get("trigger_payload") if isinstance(payload, dict) else None
    if (not isinstance(payload, dict) or payload.get("trigger") != "event"
            or not isinstance(trigger, dict) or set(trigger) - (expected_trigger.keys() | defaults.keys())
            or any(trigger.get(key) != value for key, value in expected_trigger.items())
            or any(key in trigger and trigger[key] != value for key, value in defaults.items())):
        raise RunError(ROLE_LAUNCH_HELP, outcome="needs_review")
    event = payload.get("event")
    # CustomWebhookEvent.model_dump() is the native dispatch shape. The signed
    # request is nested in payload; validate routing metadata before unwrapping.
    if isinstance(event, dict) and "payload" in event:
        if (set(event) != {"payload", "source_override", "event_key"}
                or event["source_override"] != "openspec-role-dashboard"
                or event["event_key"] != f"{stage}.requested"):
            raise RunError("Invalid native role event wrapper; source and event key must match this action")
        event = event["payload"]
    if (not isinstance(event, dict) or not ROLE_EVENT_FIELDS <= set(event) or set(event) - ROLE_EVENT_FIELDS - {"application_id", "applications", "target", "review_id", "message"}
            or event.get("schema") != "openspec-role-dashboard/v3"
            or event.get("stage") != stage or event.get("approval") != stage
            or event.get("type") != f"{stage}.requested" or event.get("role") != role):
        raise RunError("Invalid role action event; submit an explicit role and stage")
    if "application_id" in event and (not isinstance(event["application_id"], str) or len(event["application_id"]) > 80 or event["application_id"] and not CHANGE_NAME.fullmatch(event["application_id"])):
        raise RunError("Invalid application selection")
    if event["spec_store"] != config["spec_store"]:
        raise RunError("Role event spec store must match this automation's configured store")
    if not isinstance(event["requirement_id"], str) or not re.fullmatch(r"[A-Z][A-Z0-9]*-[0-9]+", event["requirement_id"]):
        raise RunError("Invalid role requirement ID")
    if not valid_spec_id(event["spec_id"], event["requirement_id"], role):
        raise RunError("Spec ID must match the selected requirement and role")
    context = role_change(event["context_change"])
    new_requirement = stage == "propose" and role == "SA" and event["context_change"] == ""
    if (event["change"] != event["spec_id"] or not new_requirement and (not context
            or context["requirement_id"] != event["requirement_id"])
            or stage != "propose" and event["context_change"] != event["change"]):
        raise RunError("Role action must bind a canonical change and context in its selected requirement")
    if (not isinstance(event["request"], str) or len(event["request"]) > 10000
            or (stage in ("propose", "update") and not event["request"].strip())):
        raise RunError("Role Propose and Update require a prompt; prompts must be at most 10000 characters")
    if stage in ("review", "commit", "merge-request"):
        if event.get("target") not in ("specs", "code") or role == "SA" and event["target"] != "specs":
            raise RunError("Choose specifications or the bound code repository; SA can deliver specifications only")
        if stage != "review" and (not delivery.canonical_id(event.get("review_id")) or not isinstance(event.get("message"), str)
                                  or not 0 < len(event["message"].strip()) <= 500 or re.search(r"[\x00-\x1f]", event["message"])):
            raise RunError("Delivery requires a selected review and one-line commit message or PR title")
    elif any(key in event for key in ("target", "review_id", "message")):
        raise RunError("Delivery inputs are only valid for Review, Commit or Merge Request")
    if "applications" in event and not new_requirement:
        raise RunError("Application bindings are only accepted when SA creates a new requirement")
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
                                   cwd=config["spec_store"], capture_output=True, timeout=20, check=False)
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


def read_role_changes(config):
    """Derive membership only from bounded, non-linked active change folders."""
    root = safe_store_file(config, Path(config["spec_store"]) / "openspec/changes")
    changes, groups = {}, {}
    try:
        with os.scandir(root) as entries:
            for count, entry in enumerate(entries, 1):
                if count > 1000:
                    raise RunError("Active change directory exceeds 1000 entries")
                if entry.name == "archive" or entry.name.startswith("."):
                    continue
                if entry.is_symlink():
                    raise RunError("Active changes must not use symlinks")
                identity = role_change(entry.name)
                if not identity:
                    if re.match(r"^(SA|FE|BE|QA)-", entry.name, re.I):
                        raise RunError("Malformed role change folder name")
                    continue
                if not entry.is_dir(follow_symlinks=False):
                    raise RunError("A role change must be a directory")
                changes[entry.name] = identity
                requirement = identity["requirement_id"]
                groups[requirement] = groups.get(requirement, 0) + 1
                if len(groups) > 50 or groups[requirement] > 20:
                    raise RunError("Store supports at most 50 requirements and 20 changes per requirement")
    except OSError:
        raise RunError("Cannot read active role change folders") from None
    return changes


def validate_role_store(config):
    stores = role_cli(config, "store", "list", "--json").get("stores", [])
    matches = [item for item in stores if isinstance(item, dict) and item.get("id") == config["store_id"]]
    if (len(matches) != 1 or not isinstance(matches[0].get("root"), str)
            or str(Path(matches[0]["root"]).resolve()) != config["spec_store"]):
        raise RunError("Registered OpenSpec store ID does not match the configured spec store")


def validate_requirement_tasks(config, changes):
    total = 0
    for name, identity in changes.items():
        if identity["requirement_id"] != config["requirement_id"]:
            continue
        path = safe_store_file(config, Path(config["spec_store"]) / "openspec/changes" / name / "tasks.md")
        if not path.exists():
            continue
        if not path.is_file() or path.stat().st_size > 64 * 1024:
            raise RunError("Role task files must be regular files of at most 64 KiB")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            raise RunError("Cannot read a role task file") from None
        total += sum(TASK_LINE.match(line) is not None for line in text.splitlines())
        if total > 500:
            raise RunError("A requirement supports at most 500 tasks across all role changes")


def role_tasks(config, *, require_ready=True):
    expected_path = Path(config["spec_store"]) / "openspec/changes" / config["change"] / "tasks.md"
    safe_store_file(config, expected_path)
    if not expected_path.is_file() or not 0 < expected_path.stat().st_size <= 64 * 1024:
        raise RunError("Selected tasks.md must be present and at most 64 KiB")
    data = role_cli(config, "instructions", "apply", "--change", config["change"],
                    "--store", config["store_id"], "--json")
    if require_ready and data.get("state") not in ("ready", "all_done"):
        raise RunError("The selected store change has incomplete or blocked planning artifacts")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks or len(tasks) > 500:
        raise RunError("The selected store change must have 1 to 500 tasks")
    selected, seen, seen_ids = [], set(), set()
    for task in tasks:
        if (not isinstance(task, dict) or not isinstance(task.get("description"), str)
                or type(task.get("done")) is not bool or task.get("sourcePath") != str(expected_path)
                or type(task.get("line")) is not int or task["line"] <= 0):
            raise RunError("OpenSpec returned tasks outside the selected role change")
        identity = (task["sourcePath"], task["description"])
        if identity in seen:
            raise RunError("Task descriptions within a selected role change must be unique")
        description = task["description"].strip()
        number = re.match(r"^(\d+(?:\.\d+)+|\d+)\.?\s+", description)
        local_id = number.group(1) if number else f"line-{task['line']}"
        if number:
            description = description[number.end():]
        role_prefix = re.match(r"^\[(SA|Frontend|Backend|QA|FE|BE)\]\s*", description)
        if role_prefix:
            tagged_role = {"FE": "Frontend", "BE": "Backend"}.get(role_prefix[1], role_prefix[1])
            if tagged_role != config["role"]:
                raise RunError("Explicit task tags must match the folder's role")
            description = description[role_prefix.end():]
            if not number:
                after = re.match(r"^(\d+(?:\.\d+)+|\d+)\.?\s+", description)
                if after:
                    local_id, description = after.group(1), description[after.end():]
        if not description.strip() or len(description) > 4000:
            raise RunError("Task descriptions must contain 1 to 4000 characters")
        if (task["sourcePath"], local_id) in seen_ids:
            raise RunError("Duplicate task IDs within a spec are not allowed")
        seen_ids.add((task["sourcePath"], local_id))
        task["role"] = config["role"]
        seen.add(identity)
        if task["sourcePath"] == str(expected_path):
            selected.append(task)
    if not selected:
        raise RunError("The selected role change must have nonempty tasks")
    return selected


ROLE_SCHEMAS = {"SA": "sa", "Frontend": "frontend", "Backend": "backend", "QA": "qa"}
UPSTREAM_ROLES = {"SA": [], "Frontend": ["SA"], "Backend": ["SA"], "QA": ["SA", "Frontend", "Backend"]}


def read_scope(config, name, seen=None):
    identity = role_change(name)
    seen = set(seen or ())
    if not identity or name in seen:
        raise RunError("Invalid or cyclic repository scope")
    seen.add(name)
    metadata = safe_store_file(config, Path(config["spec_store"]) / "openspec/changes" / name / ".openspec.yaml")
    try:
        if metadata.stat().st_size > 65536 or not re.search(r"^schema:\s*" + ROLE_SCHEMAS[identity["role"]] + r"\s*$", metadata.read_text(encoding="utf-8"), re.M):
            raise ValueError()
    except (OSError, ValueError, UnicodeError):
        raise RunError(f"{name}: schema must match its role") from None
    path = safe_store_file(config, Path(config["spec_store"]) / "openspec/changes" / name / "scope.json")
    try:
        if not path.is_file() or path.stat().st_size > 65536:
            raise ValueError()
        scope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        raise RunError(f"{name}: missing or invalid scope.json; define repository bindings before running") from None
    return validate_scope_value(config, name, scope, seen)


def validate_scope_value(config, name, scope, seen=None):
    identity = role_change(name)
    if not identity:
        raise RunError("Invalid repository scope identity")
    seen = set(seen or ())
    if not isinstance(scope, dict) or set(scope) != {"version", "applications", "references"} or type(scope["version"]) is not int or scope["version"] != 1:
        raise RunError("Invalid scope.json fields or version")
    apps, refs = scope["applications"], scope["references"]
    role = identity["role"]
    if not isinstance(apps, list) or not 1 <= len(apps) <= 20 or role != "SA" and len(apps) != 1:
        raise RunError("Downstream specs require exactly one repository; SA supports 1 to 20")
    for app in apps:
        if (not isinstance(app, dict) or set(app) != {"id", "name", "role", "repository"}
                or not isinstance(app["id"], str) or len(app["id"]) > 80 or not CHANGE_NAME.fullmatch(app["id"])
                or not isinstance(app["name"], str) or not 1 <= len(app["name"].strip()) <= 200 or re.search(r"[\x00-\x1f]", app["name"])
                or app["role"] not in ("Frontend", "Backend", "QA") or role != "SA" and app["role"] != role
                or not isinstance(app["repository"], str) or len(app["repository"]) > 500
                or not re.fullmatch(r"https://github\.com/[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_-][A-Za-z0-9_.-]*\.git", app["repository"])):
            raise RunError("Invalid application binding or HTTPS GitHub repository")
    if len({app["id"] for app in apps}) != len(apps) or len({app["repository"].lower() for app in apps}) != len(apps):
        raise RunError("Duplicate application or repository binding")
    required = UPSTREAM_ROLES[role]
    if not isinstance(refs, list) or len(refs) > 20 or any(not isinstance(ref, str) for ref in refs) or len(set(refs)) != len(refs):
        raise RunError("Invalid upstream references")
    sources = []
    for ref in refs:
        source = role_change(ref)
        if not source or source["requirement_id"] != identity["requirement_id"] or source["role"] not in required:
            raise RunError("Upstream reference must have a required role in the same requirement")
        sources.append((source["role"], read_scope(config, ref, seen)))
    if any(not any(source_role == needed for source_role, _ in sources) for needed in required):
        raise RunError("Missing required upstream role reference")
    if role != "SA" and not any(apps[0] in source["applications"] for source_role, source in sources if source_role == "SA"):
        raise RunError("Repository binding is not declared by referenced SA")
    if role == "QA":
        sa = {ref for ref in refs if role_change(ref)["role"] == "SA"}
        if any(not sa.intersection(source["references"]) for source_role, source in sources if source_role != "SA"):
            raise RunError("QA implementation references must share the referenced SA contract")
    return scope


def proposed_scope(config, changes, application_id=""):
    context = read_scope(config, config["context_change"])
    role = config["role"]
    if role_change(config["context_change"])["role"] == role and (not application_id or context["applications"][0]["id"] == application_id):
        return context
    apps = [app for app in context["applications"] if role == "SA" or app["role"] == role]
    # Context may be a single downstream spec. SA supplies the authoritative apps.
    related = [name for name, value in changes.items() if value["requirement_id"] == config["requirement_id"]]
    sa = [name for name in related if changes[name]["role"] == "SA"]
    if role != "SA":
        declared = {}
        for name in sa:
            for app in read_scope(config, name)["applications"]:
                if app["role"] != role:
                    continue
                if app["id"] in declared and declared[app["id"]] != app:
                    raise RunError("Conflicting SA application bindings; resolve them before proposing a spec")
                declared[app["id"]] = app
        apps = list(declared.values())
        if application_id:
            apps = [app for app in apps if app["id"] == application_id]
        if len(apps) != 1:
            raise RunError("Select one impacted application for this new role spec")
    if role == "SA" and sa:
        apps = list({app["id"]: app for name in sa for app in read_scope(config, name)["applications"]}.values())
    refs = [name for name in related if changes[name]["role"] in UPSTREAM_ROLES[role]]
    if any(not any(changes[name]["role"] == required for name in refs) for required in UPSTREAM_ROLES[role]):
        raise RunError("Create the required upstream role specs before proposing this role")
    return {"version": 1, "applications": apps, "references": refs}


def managed_directory(parent, name):
    parent = Path(parent)
    if parent.is_symlink() or parent.resolve() != parent or ".local" in parent.parts:
        raise RunError("Managed workspace parent must not contain symlinks or .local")
    target = parent / name
    if target.is_symlink() or target.resolve() != target:
        raise RunError("Managed workspace must not be symlinked")
    return target


def git_command(arguments, *, cwd, timeout=120):
    try:
        result = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *arguments], cwd=cwd,
                                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise RunError("Repository clone or verification failed or timed out; no conversation was started") from None
    if result.returncode:
        raise RunError("Repository clone or verification failed; check access and retry before starting a conversation")
    return result.stdout.decode("utf-8").strip()


def prepare_role_workspace(config):
    parent = Path(config["workspace"])
    parent.mkdir(parents=True, exist_ok=True)
    if config["role"] == "SA":
        # Use the store's Git identity, not the managed parent's ancestor repository.
        config["workspace_parent"] = str(parent)
        config["workspace"] = config["spec_store"]
        return config["workspace"]
    directory = managed_directory(parent, config["change"])
    directory.mkdir(exist_ok=True)
    if config.get("target") == "specs":
        target = managed_directory(directory, "planning")
        target.mkdir(exist_ok=True)
    else:
        app = config["scope"]["applications"][0]
        target = managed_directory(directory, app["id"])
        if not target.exists():
            # Clone into a fresh sibling then rename; failed clones never look reusable.
            temporary = directory / (".clone-" + str(uuid.uuid4()))
            try:
                git_command(["clone", "--", app["repository"], str(temporary)], cwd=str(directory))
                temporary.rename(target)
            finally:
                if temporary.exists():
                    shutil.rmtree(temporary)
        if not (target / ".git").is_dir() or (target / ".git").is_symlink():
            raise RunError("Managed checkout must be a standalone Git repository")
        if git_command(["rev-parse", "--show-toplevel"], cwd=str(target)) != str(target):
            raise RunError("Managed checkout root does not match the selected repository")
        if git_command(["remote", "get-url", "origin"], cwd=str(target)) != app["repository"]:
            raise RunError("Managed checkout origin does not match this spec; preserve it and resolve the mismatch")
    config["workspace_parent"] = str(parent)
    config["workspace"] = str(target)
    return str(target)


def role_preflight(config, event):
    """Validate effective event inputs and current associations under both locks."""
    config = {**config, **{key: event[key] for key in ("change", "context_change", "requirement_id", "spec_id", "request")},
              "dashboard_request_id": event["request_id"], "skill": ROLE_SKILLS[config["stage"]]}
    if "target" in event:
        config["target"] = event["target"]
    validate_role_store(config)
    changes = read_role_changes(config)
    validate_requirement_tasks(config, changes)
    context = changes.get(config["context_change"])
    new_requirement = config["stage"] == "propose" and config["role"] == "SA" and config["context_change"] == ""
    if not new_requirement and (not context or context["requirement_id"] != config["requirement_id"]):
        raise RunError("The requirement/context change association has changed; refresh the board")
    target = safe_store_file(config, Path(config["spec_store"]) / "openspec/changes" / config["change"])
    context_root = Path(config["spec_store"]) / "openspec/changes" / config["context_change"]
    for entry in context_root.rglob("*") if not new_requirement else []:
        safe_store_file(config, entry)
    if config["stage"] == "propose":
        if target.exists():
            raise RunError("The proposed spec already exists; choose a new unused feature name")
        if sum(item["requirement_id"] == config["requirement_id"] for item in changes.values()) >= 20:
            raise RunError("The requirement's 20 spec limit has been reached")
        if new_requirement:
            if any(item["requirement_id"] == config["requirement_id"] for item in changes.values()):
                raise RunError("Requirement already exists; choose its context to propose another spec")
            config["scope"] = {"version": 1, "applications": event.get("applications"), "references": []}
            validate_scope_value(config, config["change"], config["scope"], set())
        else:
            config["scope"] = proposed_scope(config, changes, event.get("application_id", ""))
    else:
        if changes.get(config["change"]) != role_change(config["spec_id"]):
            raise RunError("The selected requirement/role/spec association has changed; refresh the board")
        status = role_cli(config, "status", "--change", config["change"], "--store", config["store_id"], "--json")
        if status.get("schemaName") != ROLE_SCHEMAS[config["role"]]:
            raise RunError("Role change schema must match its folder role")
        config["scope"] = read_scope(config, config["change"])
        for entry in target.rglob("*"):
            safe_store_file(config, entry)
        if config["stage"] == "apply":
            config["selected_tasks"] = role_tasks(config)
    config["related_changes"] = sorted(name for name, item in changes.items() if item["requirement_id"] == config["requirement_id"])
    return config, changes


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


def checked_task_descriptions(content):
    return {match[2].strip() for line in content.splitlines()
            if (match := TASK_LINE.match(line)) and (match[1] or "").lower() == "x"}


def audit_role_scope(config, before_store, before_workspace, before_tasks, result):
    changed = changed_paths(before_store, scope_snapshot(config["spec_store"]))
    prefix = f"openspec/changes/{config['change']}/"
    task_path = prefix + "tasks.md"
    def allowed(path):
        if config["stage"] == "apply":
            return path == task_path
        return path in {task_path, prefix + "proposal.md", prefix + "design.md"} or (
            path.startswith(prefix) and re.fullmatch(r"specs/(?:[A-Za-z0-9_-]+/)+spec\.md", path[len(prefix):]) is not None)
    if any(not allowed(path) for path in changed):
        raise RunError("Role action changed files outside its permitted store scope; inspect the conversation and preserve recovery evidence")
    for entry in (Path(config["spec_store"]) / prefix).rglob("*"):
        safe_store_file(config, entry)
    parent = config.get("workspace_parent", config["workspace"])
    after_workspace = scope_snapshot(parent)
    workspace_changes = changed_paths(before_workspace, after_workspace)
    if config["stage"] != "apply" or config["role"] == "SA":
        if workspace_changes:
            raise RunError("Planning action or SA changed implementation files; inspect the conversation before continuing")
    else:
        prefix_workspace = str(Path(config["workspace"]).relative_to(parent)) + "/"
        if any(not path.startswith(prefix_workspace) for path in workspace_changes):
            raise RunError("Apply changed another repository outside its selected workspace")
    if config["stage"] != "apply":
        path = safe_store_file(config, Path(config["spec_store"]) / task_path)
        if path.exists():
            if not path.is_file() or path.stat().st_size > 64 * 1024:
                raise RunError("Selected tasks.md must be a regular file of at most 64 KiB")
            checked = checked_task_descriptions(path.read_text(encoding="utf-8"))
            if config["stage"] == "propose" and checked:
                raise RunError("A new proposal must start with all selected spec tasks unchecked")
            if config["stage"] == "update" and checked - checked_task_descriptions(before_tasks):
                raise RunError("Update must not newly complete tasks or transfer completion to revised task text")
    if config["stage"] == "apply":
        path = safe_store_file(config, Path(config["spec_store"]) / task_path)
        if not path.is_file() or not 0 < path.stat().st_size <= 64 * 1024:
            raise RunError("Apply removed its tasks.md or made it empty or oversized")
        after = path.read_text(encoding="utf-8")
        old_lines, new_lines = before_tasks.splitlines(keepends=True), after.splitlines(keepends=True)
        if len(old_lines) != len(new_lines):
            raise RunError("Apply may change selected role checkboxes only, not task structure")
        newly_done, reopened = set(), set()
        selected_lines = {task["line"]: task for task in config["selected_tasks"]}
        for number, (old, new) in enumerate(zip(old_lines, new_lines), start=1):
            if old == new:
                continue
            task = selected_lines.get(number)
            pattern = r"^(\s*(?:[-*+]|\d{1,9}[.)])\s*\[)(\s*\S?\s*)(\].*)$"
            a, b = re.match(pattern, old.rstrip("\r\n")), re.match(pattern, new.rstrip("\r\n"))
            if (not task or not a or not b or a.group(1, 3) != b.group(1, 3)
                    or old[len(old.rstrip("\r\n")):] != new[len(new.rstrip("\r\n")):]):
                raise RunError(f"Apply changed selected task text or structure at line {number}; only completion markers may change")
            marker = b.group(2).strip().lower()
            if marker not in ("", "x"):
                raise RunError(f"Apply used an unsupported task marker at line {number}")
            if task["done"] and marker == "":
                reopened.add(task["description"])
            elif not task["done"] and marker == "x":
                newly_done.add(task["description"])
        corrections = result.get("task_corrections", [])
        if not isinstance(corrections, list):
            raise RunError("Apply task_corrections must be an array")
        explained = {entry["task"] for entry in corrections if isinstance(entry, dict)
                     and isinstance(entry.get("task"), str) and isinstance(entry.get("reason"), str)
                     and entry["reason"].strip()}
        if reopened - explained:
            raise RunError("Apply reopened a completed task without an exact task_corrections reason")
        evidence = result.get("task_evidence", [])
        if not isinstance(evidence, list):
            raise RunError("Apply task evidence must be an array")
        evidenced = {entry["task"] for entry in evidence if isinstance(entry, dict)
                     and isinstance(entry.get("task"), str) and isinstance(entry.get("evidence"), str)
                     and entry["evidence"].strip()}
        if newly_done - evidenced:
            raise RunError("Apply checked tasks without concrete task_evidence in its final result")


def validate_role_result(config, changes, before_tasks, result):
    if result["status"] != "completed":
        return result
    read_scope(config, config["change"])
    current = read_role_changes(config)
    validate_requirement_tasks(config, current)
    root = Path(config["spec_store"]) / "openspec/changes" / config["change"]
    specs = list((root / "specs").rglob("spec.md"))
    if not 1 <= len(specs) <= 20:
        raise RunError("The selected role change must have 1 to 20 capability specifications")
    for relative in ("proposal.md", "design.md", "tasks.md", *(str(path.relative_to(root)) for path in specs)):
        artifact = safe_store_file(config, root / relative)
        if not artifact.is_file() or not 0 < artifact.stat().st_size <= 64 * 1024 or not artifact.read_text(encoding="utf-8").strip():
            raise RunError("The selected spec must have nonempty specification and task artifacts of at most 64 KiB")
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
    if config["stage"] == "propose":
        if current != {**changes, config["change"]: role_change(config["change"])}:
            raise RunError("Other role change folders changed during Propose; inspect the conversation")
        result = {**result, "requirement_id": config["requirement_id"], "spec_id": config["spec_id"],
                  "summary": f"Planned {config['spec_id']} under {config['requirement_id']}. " + result["summary"]}
    return result


def run_role(client, config, event, prompt, env):
    deadline = time.monotonic() + config["timeout_seconds"]
    # Deterministic order prevents two role runs that share either root deadlocking.
    with contextlib.ExitStack() as stack:
        for path in sorted({config["workspace"], config["spec_store"]}):
            stack.enter_context(workspace_lock(path))
        effective, changes = role_preflight(config, event)
        config.update(effective)
        claim_dashboard_request(event, Path.home() / ".openhands/apps/openspec-progress/role-consumed")
        prepare_role_workspace(config)
        if config["stage"] in ("review", "commit", "merge-request"):
            try:
                if config["stage"] == "review":
                    review = delivery.create_review(config, event["target"], env.get("AUTOMATION_RUN_ID", ""))
                    return {"status": "completed", "summary": f"Reviewed {len(review['files'])} files in {event['target']}. Snapshot {review['id']}.",
                            "findings": [], "next_action": "Inspect the review diff in this role app, then choose Commit or Merge Request."}
                receipt = delivery.deliver(config, event["review_id"], event["target"], config["stage"], event["message"])
                return {"status": "completed", "summary": f"Committed {receipt['commit']} on {receipt['branch']}." + (" " + receipt["url"] if "url" in receipt else " Local commit; nothing pushed."),
                        "findings": [], "next_action": "Open the delivery receipt in this role app."}
            except delivery.DeliveryError as error:
                raise RunError(str(error), outcome="needs_review") from None
        before_spec = delivery.spec_snapshot(config)
        result = None
        try:
            if config["stage"] == "propose":
                # Existing-directory commands accept uppercase; `new change` does not.
                # Exclusive creation under the store lock never overwrites another change.
                target = safe_store_file(config, Path(config["spec_store"]) / "openspec/changes" / config["change"])
                target.mkdir()
                (target / ".openspec.yaml").write_text("schema: " + ROLE_SCHEMAS[config["role"]] + "\n", encoding="utf-8")
                (target / "scope.json").write_text(json.dumps(config["scope"], indent=2) + "\n", encoding="utf-8")
                read_scope(config, config["change"])
            before_store = scope_snapshot(config["spec_store"])
            before_workspace = scope_snapshot(config["workspace_parent"])
            task_path = Path(config["spec_store"]) / "openspec/changes" / config["change"] / "tasks.md"
            before_tasks = task_path.read_text(encoding="utf-8") if task_path.exists() else ""
            prompt += "\n\nRun configuration (data for this explicitly selected role action):\n" + json.dumps(config, indent=2)
            if time.monotonic() >= deadline:
                raise RunError("Workspace preparation exceeded the run timeout; no conversation was started")
            # Role profile selection is fixed by configuration, not injected per-run overrides.
            result = client.run(config, prompt, run_id=env.get("AUTOMATION_RUN_ID", ""), deadline=deadline)
            try:
                audit_role_scope(config, before_store, before_workspace, before_tasks, result)
                result = validate_role_result(config, changes, before_tasks, result)
            except (RunError, OSError, UnicodeError) as error:
                if not isinstance(error, RunError):
                    error = RunError("Role artifact audit could not read the expected UTF-8 source; inspect missing or invalid files")
                result = {"status": "blocked", "outcome": "execution_error", "summary": str(error),
                          "findings": [], "agent_result": result, "audit_errors": [str(error)]}
            return result
        finally:
            delivery.save_revision(config, before_spec, (result or {}).get("outcome", (result or {}).get("status", "execution_error")), env.get("AUTOMATION_RUN_ID", ""))


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
    if set(result) - {"status", "summary", "findings", "task_evidence", "task_corrections", "blocker_type", "next_action"}:
        raise RunError("Agent terminal JSON contains unsupported fields")
    if (result.get("blocker_type") not in (None, "dependency", "input")
            or ("next_action" in result and (not isinstance(result["next_action"], str) or not result["next_action"].strip()))):
        raise RunError("Agent terminal JSON has invalid blocker or next-action details")
    for field, detail in (("task_evidence", "evidence"), ("task_corrections", "reason")):
        if field in result and (not isinstance(result[field], list) or len(result[field]) > 500 or any(
                not isinstance(entry, dict) or set(entry) != {"task", detail}
                or not all(isinstance(entry[key], str) and entry[key].strip() for key in ("task", detail))
                for entry in result[field])):
            raise RunError(f"Agent terminal JSON has invalid {field}")
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
        tags = {"openspecstage": config["stage"], "automationrunid": run_id,
                "automationtrigger": "automation"}
        role_run = config.get("mode") == "role"
        if role_run:
            tags.update(requirement=config["requirement_id"], role=config["role"], openspecspec=config["spec_id"])
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
                                     body={"title": config["spec_id"]})
                if named.get("success") is not True:
                    raise RunError("OpenHands could not save the role conversation title")
                started = self.request(path + "/events", method="POST", deadline=deadline, body=message)
                if started.get("success") is not True:
                    raise RunError("OpenHands could not start the named role conversation")
            while True:
                state = self.request(path, deadline=deadline)
                status = state.get("execution_status")
                if status in ("error", "stuck", "paused", "waiting_for_confirmation"):
                    raise RunError(f"Conversation requires attention: {status}", outcome=
                                   "needs_review" if status in ("paused", "waiting_for_confirmation") else "execution_error")
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
    for name in ("SESSION_API_KEY", "OH_SESSION_API_KEYS_0", "AUTOMATION_CALLBACK_API_KEY", "OPENHANDS_AUTOMATION_API_KEY"):
        if env.get(name):
            text = text.replace(env[name], "[redacted]")
    return text


def run_outcome(result, env):
    """Project only bounded, redacted diagnostics; never copy arbitrary run metadata."""
    agent = result.get("agent_result", result)
    kind = result.get("outcome") or {"completed": "completed", "blocked": "blocked", "findings": "needs_review"}[result["status"]]
    next_action = {
        "completed": "Refresh the requirement to read verified source changes.",
        "blocked": "Resolve the reported blocker, then explicitly submit the automation again from its role workflow.",
        "needs_review": "Open the conversation to resolve findings or required confirmation before submitting more work.",
        "execution_error": "Inspect the audit details and linked run, resolve the error, then submit explicitly from its role workflow.",
    }[kind]
    def bounded(value, limit):
        return redact(value, env).replace("\x00", "")[:limit]
    def messages(values):
        # Structured findings must opt into a human-readable message; other keys are private.
        return [bounded(value if isinstance(value, str) else value["message"], 1000)
                for value in values if isinstance(value, str) or isinstance(value, dict) and isinstance(value.get("message"), str)][:8]
    return {"status": kind, "blocker_type": agent.get("blocker_type") if kind == "blocked" else None,
            "summary": bounded(agent["summary"], 2000), "findings": messages(agent["findings"]),
            "audit_errors": messages(result.get("audit_errors", [])),
            "next_action": bounded(next_action if kind == "execution_error" else agent.get("next_action") or next_action, 1000),
            "agent_status": agent["status"] if "agent_result" in result else None}


def save_role_outcome(config, event, result, env, conversation_id):
    """Atomically persist a per-run result for the read-only Agent Server bridge."""
    run_id = env.get("AUTOMATION_RUN_ID", "")
    try:
        if str(uuid.UUID(run_id)) != run_id:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise RunError("Cannot record role result without a canonical native run ID") from None
    root = Path.home().resolve() / ".openhands/apps/openspec-progress/role-results"
    if root.resolve() != root:
        raise RunError("Role result directory must not be symlinked")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    report = {"version": 1, "run_id": run_id, "conversation_id": conversation_id,
              "role": config["role"], "stage": config["stage"],
              "requirement_id": event.get("requirement_id"), "spec_id": event.get("spec_id"),
              "configuration": {key: config[key] for key in
                                ("workspace", "spec_store", "store_id", "profile", "skill_root", "timeout_seconds")},
              "outcome": run_outcome(result, env)}
    raw = json.dumps(report, ensure_ascii=False).encode("utf-8")
    if len(raw) > 64 * 1024:
        raise RunError("Role result exceeded its size limit")
    descriptor, temporary = tempfile.mkstemp(prefix=".result-", dir=root)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, root / (run_id + ".json"))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None, *, env=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    parser.add_argument("--prompt", type=Path, default=Path(__file__).with_name("prompt.md"))
    parser.add_argument("--check", action="store_true", help="Validate local prerequisites without starting a conversation")
    args = parser.parse_args(argv)
    env = dict(os.environ if env is None else env)
    client = None
    result = None
    config, dashboard_input = None, {}
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
                read_role_changes(config)
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
        result = {"status": "blocked", "summary": str(error) or "OpenSpec stage interrupted", "findings": [],
                  "outcome": getattr(error, "outcome", "execution_error")}
    except Exception:
        # Arbitrary HTTP bodies, settings, and exception reprs can contain secrets.
        result = {"status": "blocked", "outcome": "execution_error",
                  "summary": "Unexpected runner failure; inspect the local runner and conversation", "findings": []}
    finally:
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)
    if result is None:
        return 1
    result = json.loads(redact(json.dumps(result), env))
    if not args.check and config and config.get("mode") == "role":
        try:
            save_role_outcome(config, dashboard_input, result, env, client.conversation_id if client else None)
        except Exception:
            result = {"status": "blocked", "outcome": "execution_error", "agent_result": result,
                      "summary": "Could not save structured role result; inspect native run logs", "findings": [],
                      "audit_errors": ["Could not save structured role result; inspect native run logs"]}
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
