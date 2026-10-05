"""Automation-owned revision evidence and deterministic, reviewed Git delivery."""

import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
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


def command(arguments, cwd, *, env=None, check=True):
    try:
        result = subprocess.run(arguments, cwd=cwd, env={**os.environ, "GIT_TERMINAL_PROMPT": "0",
                                "GIT_LITERAL_PATHSPECS": "1", **(env or {})},
                                capture_output=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise DeliveryError("Git delivery command failed or timed out; inspect the recorded delivery before retrying") from None
    require(len(result.stdout) <= MAX_BYTES * 3, "Git output exceeds the review size limit")
    if check:
        require(result.returncode == 0, "Git delivery command failed; check repository access, Git identity and gh authentication")
    return result


def git(root, *arguments, env=None):
    return command(["git", *arguments], root, env=env).stdout


def review_repository(config, target):
    identity(config)
    require(target in ("specs", "code") and not (config["role"] == "SA" and target == "code"),
            "SA can review and deliver its own specifications only")
    root = Path(config["spec_store"] if target == "specs" else config["workspace"])
    require(root.resolve() == root and root.is_dir(), "Review repository is unavailable or symlinked")
    require(git(root, "rev-parse", "--show-toplevel").decode().strip() == str(root), "Review requires the selected Git repository root")
    origin = git(root, "remote", "get-url", "origin").decode().strip()
    require(re.fullmatch(r"https://github\.com/[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_-][A-Za-z0-9_.-]*\.git", origin),
            "Delivery requires a credential-free HTTPS GitHub origin")
    if target == "code":
        require(origin == config["scope"]["applications"][0]["repository"], "Review repository differs from the selected spec binding")
    branch = git(root, "symbolic-ref", "--short", "HEAD").decode().strip()
    head = git(root, "rev-parse", "HEAD").decode().strip()
    prefix = "openspec/changes/" + config["spec_id"] + "/" if target == "specs" else "."
    raw = git(root, "diff", "--no-renames", "--name-only", "-z", "HEAD", "--", prefix)
    raw += git(root, "ls-files", "--others", "--exclude-standard", "-z", "--", prefix)
    try:
        names = sorted({name.decode("utf-8") for name in raw.split(b"\0") if name})
    except UnicodeError:
        raise DeliveryError("Review paths must use UTF-8") from None
    require(len(names) <= MAX_FILES, "Review exceeds its file count limit")
    files, size = [], 0
    for name in names:
        path = safe_path(root, name)
        entry = git(root, "ls-tree", "-z", "HEAD", "--", name)
        before = None
        if entry:
            mode = entry.split(b" ", 1)[0].decode()
            require(mode in ("100644", "100755"), "Linked files and submodules cannot be delivered")
            before = {"mode": mode, "data": git(root, "show", "HEAD:" + name)}
        after = file_value(path)
        size += len((before or {}).get("data", b"")) + len((after or {}).get("data", b""))
        require(size <= MAX_BYTES, "Review exceeds its content size limit")
        files.append(diff_file(name, before, after))
    snapshot = {"target": target, "repository": str(root), "origin": origin, "branch": branch, "head": head, "files": files}
    snapshot["fingerprint"] = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
    return snapshot


def create_review(config, target, run_id):
    snapshot = review_repository(config, target)
    record = {"id": str(uuid.uuid4()), "context": identity(config), "created_at": now(),
              "run_id": run_id if canonical_id(run_id) else None, **snapshot}
    return save_record(config, "reviews", record)


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


def commit_review(root, review, message):
    paths = [file["path"] for file in review["files"]]
    require(paths, "There are no reviewed changes to commit")
    with tempfile.TemporaryDirectory(prefix="openspec-index-") as directory:
        environment = {"GIT_INDEX_FILE": str(Path(directory) / "index")}
        git(root, "read-tree", "HEAD", env=environment)
        git(root, "add", "-A", "--", *paths, env=environment)
        tree = git(root, "write-tree", env=environment).decode().strip()
        # Commit an immutable, verified tree. No working-tree hook can substitute
        # unreviewed bytes between review and the Git commit operation.
        verify_tree(root, review, tree)
        commit = git(root, "commit-tree", tree, "-p", review["head"], "-m", message).decode().strip()
        git(root, "update-ref", "-m", "OpenSpec: " + message, "HEAD", commit, review["head"])
    # Reset only the committed paths in the real index; preserve other staging.
    git(root, "reset", "-q", "HEAD", "--", *paths)
    return commit


def verify_tree(root, review, tree):
    actual = git(root, "diff-tree", "--no-renames", "--name-only", "-r", "-z", review["head"], tree)
    require(set(actual.decode().strip("\0").split("\0")) == {file["path"] for file in review["files"]},
            "Staged paths changed during delivery; run Review again")
    for file in review["files"]:
        entry = git(root, "ls-tree", "-z", tree, "--", file["path"])
        if file["after"] is None:
            require(not entry, "Deleted file reappeared during delivery")
        else:
            require(entry and entry.split(b" ", 1)[0].decode() == file["after_mode"], "File mode changed during delivery")
            content = git(root, "show", tree + ":" + file["path"])
            require(hashlib.sha256(content).hexdigest() == file["after"], "File content changed during delivery; run Review again")


def deliver(config, review_id, target, stage, message):
    require(stage in ("commit", "merge-request"), "Unsupported delivery action")
    require(isinstance(message, str) and 0 < len(message.strip()) <= 500 and not re.search(r"[\x00-\x1f]", message),
            "Enter a one-line commit message or PR title of at most 500 characters")
    review = load_record(config, "reviews", review_id)
    require(review["target"] == target, "Selected review belongs to another target")
    require(not (config["role"] == "SA" and target != "specs"), "SA cannot deliver code")
    root = Path(review["repository"])
    expected_root = config["spec_store"] if target == "specs" else config["workspace"]
    require(str(root) == expected_root and root.resolve() == root, "Review repository no longer matches this workspace")
    if target == "code":
        require(review["origin"] == config["scope"]["applications"][0]["repository"], "Reviewed repository binding changed")
    receipt_path = state_root(config) / "deliveries" / (review_id + ".json")
    if receipt_path.exists():
        receipt = load_record(config, "deliveries", review_id)
        require(receipt["stage"] == stage and receipt["message"] == message, "This review already has another delivery; use its existing receipt")
        if receipt["state"] == "complete":
            return receipt
        require(receipt.get("commit"), "An earlier commit outcome is uncertain; inspect Git history before retrying")
        require(git(root, "rev-parse", "HEAD").decode().strip() == receipt["commit"]
                and git(root, "symbolic-ref", "--short", "HEAD").decode().strip() == receipt["branch"]
                and git(root, "remote", "get-url", "origin").decode().strip() == review["origin"],
                "Repository moved after partial delivery; inspect the saved receipt")
    else:
        current = review_repository(config, target)
        require(current["fingerprint"] == review["fingerprint"], "Files, branch, HEAD or origin changed after review; run Review again")
        require(review["files"], "There are no reviewed changes to deliver")
        branch = review["branch"] if stage == "commit" else "codex/" + config["spec_id"].lower() + "-" + review_id[:8]
        receipt = {"id": review_id, "context": identity(config), "created_at": now(), "stage": stage,
                   "target": target, "message": message, "branch": branch, "base": review["branch"], "state": "committing"}
        save_record(config, "deliveries", receipt)
        if stage == "merge-request":
            git(root, "switch", "-c", branch)
        receipt["commit"] = commit_review(root, review, message)
        receipt["state"] = "committed"
        save_record(config, "deliveries", receipt)
    if stage == "merge-request":
        owner_repo = review["origin"].removeprefix("https://github.com/").removesuffix(".git")
        git(root, "push", review["origin"], receipt["commit"] + ":refs/heads/" + receipt["branch"])
        receipt["state"] = "pushed"
        save_record(config, "deliveries", receipt)
        existing = command(["gh", "pr", "list", "--repo", owner_repo, "--head", receipt["branch"],
                            "--base", receipt["base"], "--state", "all", "--json", "url", "--limit", "2"], root)
        try:
            rows = json.loads(existing.stdout)
            require(isinstance(rows, list) and len(rows) <= 1, "Ambiguous PR history for this delivery branch")
            url = rows[0]["url"] if rows else None
        except (ValueError, KeyError, TypeError):
            raise DeliveryError("GitHub returned invalid PR history; inspect the pushed branch before retrying") from None
        if not url:
            with tempfile.TemporaryDirectory(prefix="openspec-pr-") as directory:
                body = Path(directory) / "body.md"
                body.write_text(f"Implements {config['spec_id']} ({config['role']}).\n\nReviewed snapshot: {review_id}\nCommit: {receipt['commit']}\n", encoding="utf-8")
                url = command(["gh", "pr", "create", "--repo", owner_repo, "--base", receipt["base"], "--head", receipt["branch"],
                               "--title", message, "--body-file", str(body)], root).stdout.decode().strip()
        require(isinstance(url, str) and re.fullmatch(r"https://github\.com/" + re.escape(owner_repo) + r"/pull/[0-9]+", url),
                "GitHub returned an unexpected pull request URL; inspect the recorded branch")
        receipt["url"] = url
    receipt["state"] = "complete"
    return save_record(config, "deliveries", receipt)
