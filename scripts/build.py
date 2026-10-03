#!/usr/bin/env python3
"""Build independent OpenHands Git Sync bundles from the shared sources."""

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


STAGES = ("explore", "propose", "update", "apply", "verify", "sync", "archive")
ROLE_STAGES = ("propose", "update", "apply")
ROLE_FIELDS = {"workspace", "spec_store", "store_id", "skill_root", "profile", "timeout_seconds", "canvas_url"}
ROLES = ("SA", "Frontend", "Backend", "QA")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Cannot read {path}: {error}") from error


def json_text(value: dict) -> str:
    # JSON is a YAML subset, so the generator needs no YAML dependency.
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def load_role_config(root: Path) -> dict:
    try:
        config = json.loads(read_text(root / "role-workflow.json"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid role-workflow.json: {error}") from error
    if not isinstance(config, dict) or set(config) != ROLE_FIELDS:
        raise ValueError("role-workflow.json must contain exactly: " + ", ".join(sorted(ROLE_FIELDS)))
    for key in ROLE_FIELDS - {"timeout_seconds"}:
        if not isinstance(config[key], str) or not config[key].strip():
            raise ValueError(f"Role {key} must be nonempty text")
    for key in ("workspace", "spec_store", "skill_root"):
        if not Path(config[key]).is_absolute() or ".local" in Path(config[key]).parts:
            raise ValueError(f"Role {key} must be an absolute path outside .local")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", config["store_id"]):
        raise ValueError("Role store_id must be lowercase kebab-case")
    if type(config["timeout_seconds"]) is not int or not 60 <= config["timeout_seconds"] <= 1800:
        raise ValueError("Role timeout_seconds must be an integer from 60 to 1800")
    url = urlsplit(config["canvas_url"])
    try:
        valid = (url.scheme in ("http", "https") and url.hostname in ("localhost", "127.0.0.1", "::1")
                 and not url.username and not url.password and not url.query and not url.fragment
                 and url.path in ("", "/"))
        url.port
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Role canvas_url must be a loopback HTTP(S) origin")
    return config


def expected_files(root: Path) -> dict[Path, str]:
    """Read and validate all sources before any generated files are written."""
    runtime = read_text(root / "runtime" / "run.py")
    if not runtime.strip():
        raise ValueError("runtime/run.py must not be empty")
    expected = {}
    role_config = load_role_config(root)
    role_common = read_text(root / "prompts" / "role-common.md").strip()
    if not role_common:
        raise ValueError("prompts/role-common.md must not be empty")
    for role, stage in ((role, stage) for role in ROLES for stage in ROLE_STAGES):
        prompt = read_text(root / "prompts" / f"role-{stage}.md").strip()
        if not prompt:
            raise ValueError(f"prompts/role-{stage}.md must not be empty")
        directory = Path("automations") / f"openspec-{role.lower()}-{stage}"
        expected[directory / "automation.yaml"] = json_text({
            "name": f"OpenSpec {role} · {stage.title()}", "state": "ACTIVE", "enabled": True,
            "trigger": {"type": "event", "source": "openspec-role-dashboard", "on": f"{stage}.requested",
                        "filter": f"schema == 'openspec-role-dashboard/v1' && stage == '{stage}' && approval == '{stage}' && role == '{role}'"},
            "entrypoint": "python3 run.py", "timeout": role_config["timeout_seconds"],
            "keep_alive": False, "tarball_source": {"type": "internal"},
        })
        expected[directory / "tarball" / "run.py"] = runtime
        expected[directory / "tarball" / "config.json"] = json_text({**role_config, "mode": "role", "stage": stage, "role": role})
        expected[directory / "tarball" / "prompt.md"] = f"{role_common}\n\n{prompt}\n"
    return expected


def build(root: Path, *, check: bool = False) -> list[Path]:
    expected = expected_files(root)
    directory = root / "automations"
    allowed = {path.parts[1] for path in expected}
    unexpected = sorted(path.name for path in directory.iterdir() if path.name not in allowed) if directory.exists() else []
    if unexpected:
        raise ValueError("Move retired or unrelated definitions outside automations/: " + ", ".join(unexpected))
    changed = []
    for relative_path, content in expected.items():
        path = root / relative_path
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            changed.append(relative_path)
    if not check:
        for relative_path in changed:
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected[relative_path], encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated bundles are missing or stale")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        changed = build(root, check=args.check)
    except (ValueError, OSError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1
    if args.check and changed:
        print("Generated bundles are missing or stale; run npm run build:", file=sys.stderr)
        for path in changed:
            print(f"  {path}", file=sys.stderr)
        return 1
    if args.check:
        print("All 12 dedicated role/skill bundles match their sources.")
    else:
        print(f"Built 12 OpenSpec bundles ({len(changed)} files updated).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
