"""Automation-owned spec revisions and read-only historical delivery evidence."""

import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from datetime import datetime, timezone
import uuid


MAX_BYTES = 2 * 1024 * 1024
MAX_FILES = 200
ROLE_PREFIX = {"SA": "SA", "Frontend": "FE", "Backend": "BE", "QA": "QA"}


class DeliveryError(Exception):
    """A bounded explanation safe to return to the role app."""


def require(condition, message):
    if not condition:
        raise DeliveryError(message)


def canonical_id(value):
    try:
        return isinstance(value, str) and str(uuid.UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def identity(config):
    role, spec = config.get("role"), config.get("spec_id")
    requirement = config.get("requirement_id")
    require(role in ROLE_PREFIX and isinstance(requirement, str)
            and re.fullmatch(r"[A-Z][A-Z0-9]*-[0-9]+", requirement), "Invalid delivery role or requirement")
    require(isinstance(spec, str) and len(spec) <= 160
            and re.fullmatch(re.escape(ROLE_PREFIX[role] + "-" + requirement + "-") + r"[a-z0-9]+(?:-[a-z0-9]+)*", spec),
            "Delivery spec must belong to the selected requirement and role")
    store = Path(config["spec_store"])
    require(store.is_absolute() and store.resolve() == store and ".local" not in store.parts,
            "Invalid delivery store")
    return {"spec_store": str(store), "role": role, "requirement_id": requirement, "spec_id": spec}


def safe_path(root, relative):
    require(isinstance(relative, str) and relative and not re.search(r"[\x00-\x1f]", relative), "Unsupported file path in review")
    parts = Path(relative).parts
    require(not Path(relative).is_absolute() and not set(parts) & {"..", ".git", ".local"}, "File is outside the review scope")
    path = Path(root) / relative
    require(path.resolve() == path and not path.is_symlink(), "Linked files cannot be reviewed or delivered")
    return path


def state_root(config):
    context = identity(config)
    store_key = hashlib.sha256(context["spec_store"].encode()).hexdigest()[:24]
    root = Path.home().resolve() / ".openhands/role-delivery" / store_key / context["spec_id"]
    require(root.resolve() == root, "Delivery state must not be symlinked")
    return root


def save_record(config, kind, value):
    root = state_root(config) / kind
    require(root.resolve() == root, "Delivery state must not be symlinked")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    raw = json.dumps(value, ensure_ascii=False).encode()
    require(len(raw) <= MAX_BYTES * 3, "Delivery record exceeds its size limit")
    descriptor, temporary = tempfile.mkstemp(prefix=".record-", dir=root)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, root / (value["id"] + ".json"))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return value


def load_record(config, kind, record_id):
    require(kind in ("revisions", "reviews", "deliveries") and canonical_id(record_id), "Invalid delivery record selection")
    root = state_root(config)
    path = safe_path(root, kind + "/" + record_id + ".json")
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES * 3 + 1)
        require(len(raw) <= MAX_BYTES * 3, "Delivery record exceeds its size limit")
        value = json.loads(raw)
    except (OSError, ValueError):
        raise DeliveryError("The selected record is unavailable; refresh this role workspace") from None
    require(isinstance(value, dict) and value.get("id") == record_id and value.get("context") == identity(config),
            "Delivery record does not match the selected role, store and spec")
    return value


def now():
    return datetime.now(timezone.utc).isoformat()


def file_value(path):
    if not path.exists():
        return None
    require(path.is_file() and path.stat().st_size <= MAX_BYTES, "Only bounded regular files can be reviewed")
    raw = path.read_bytes()
    require(len(raw) <= MAX_BYTES, "Review file exceeds its size limit")
    return {"data": raw, "mode": "100755" if path.stat().st_mode & 0o111 else "100644"}


def diff_file(name, before, after):
    old, new = (before or {}).get("data", b""), (after or {}).get("data", b"")
    binary = b"\0" in old or b"\0" in new
    try:
        old_text, new_text = old.decode("utf-8"), new.decode("utf-8")
    except UnicodeError:
        binary = True
    status = "added" if before is None else "deleted" if after is None else "modified"
    patch = f"Binary file {status}: {name}\n" if binary else "".join(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n" for line in difflib.unified_diff(
        old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
        fromfile="/dev/null" if before is None else "a/" + name,
        tofile="/dev/null" if after is None else "b/" + name))
    old_mode, new_mode = (before or {}).get("mode"), (after or {}).get("mode")
    if old_mode != new_mode:
        patch = f"Mode: {old_mode or 'absent'} → {new_mode or 'absent'}\n" + patch
    return {"path": name, "status": status, "binary": binary, "diff": patch,
            "before": None if before is None else hashlib.sha256(old).hexdigest(),
            "after": None if after is None else hashlib.sha256(new).hexdigest(),
            "before_mode": old_mode, "after_mode": new_mode}


def spec_snapshot(config):
    identity(config)
    root = Path(config["spec_store"])
    change = safe_path(root, "openspec/changes/" + config["spec_id"])
    result, size = {}, 0
    for path in sorted(change.rglob("*")) if change.exists() else []:
        relative = path.relative_to(root).as_posix()
        safe_path(root, relative)
        if path.is_dir():
            continue
        value = file_value(path)
        size += len(value["data"])
        require(len(result) < MAX_FILES and size <= MAX_BYTES, "Specification revision exceeds its size limit")
        result[relative] = value
    return result


def save_revision(config, before, outcome, run_id):
    after = spec_snapshot(config)
    files = [diff_file(path, before.get(path), after.get(path)) for path in sorted(before.keys() | after.keys())
             if before.get(path) != after.get(path)]
    if not files:
        return None
    record = {"id": str(uuid.uuid4()), "context": identity(config), "created_at": now(),
              "stage": config["stage"], "run_id": run_id if canonical_id(run_id) else None,
              "outcome": outcome, "files": files}
    return save_record(config, "revisions", record)


def history(config):
    root = state_root(config)
    result = {"revisions": [], "reviews": [], "deliveries": []}
    for kind in result:
        directory = root / kind
        require(directory.resolve() == directory, "History directory must not be symlinked")
        paths = list(directory.glob("*.json")) if directory.exists() else []
        require(len(paths) <= 5000, "History exceeds its record limit")
        # Newest files first, returning metadata only; select a record to fetch its diff.
        for path in sorted(paths, key=lambda item: item.stat().st_mtime_ns, reverse=True)[:50]:
            row = load_record(config, kind, path.stem)
            result[kind].append({key: row[key] for key in ("id", "created_at", "stage", "run_id", "outcome", "target", "commit", "branch", "url", "state") if key in row}
                                | {"file_count": len(row.get("files", []))})
    return result



def save_conversation_link(config, conversation_id, run_id):
    """Record the exact spec association before the role conversation starts work."""
    require(canonical_id(conversation_id) and canonical_id(run_id), "Invalid role conversation identity")
    root = Path.home().resolve() / ".openhands/apps/openspec-progress/role-conversations"
    require(root.resolve() == root, "Conversation state must not be symlinked")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    value = {"version": 1, "run_id": run_id, "conversation_id": conversation_id,
             "context": identity(config), "stage": config["stage"]}
    descriptor, temporary = tempfile.mkstemp(dir=root)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, root / (run_id + ".json"))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
