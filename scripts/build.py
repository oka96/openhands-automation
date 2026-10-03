#!/usr/bin/env python3
"""Build independent OpenHands Git Sync bundles from the shared sources."""

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


STAGES = ("explore", "propose", "update", "apply", "verify", "sync", "archive")
CONFIG_FIELDS = {
    "workspace", "change", "request", "profile", "timeout_seconds", "canvas_url"
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Cannot read {path}: {error}") from error


def load_config(root: Path) -> dict:
    try:
        config = json.loads(read_text(root / "workflow.json"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid workflow.json: {error}") from error
    if not isinstance(config, dict) or set(config) != CONFIG_FIELDS:
        raise ValueError("workflow.json must contain exactly: " + ", ".join(sorted(CONFIG_FIELDS)))
    for key in ("workspace", "change", "request", "profile", "canvas_url"):
        if not isinstance(config[key], str):
            raise ValueError(f"{key} must be a string")
    if not Path(config["workspace"]).is_absolute():
        raise ValueError("workspace must be an absolute path on the Agent Server host")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", config["change"]):
        raise ValueError("change must be a lowercase kebab-case OpenSpec change name")
    if not config["profile"].strip():
        raise ValueError("profile must not be blank")
    timeout = config["timeout_seconds"]
    if type(timeout) is not int or not 60 <= timeout <= 1800:
        raise ValueError("timeout_seconds must be an integer from 60 to 1800")
    try:
        url = urlsplit(config["canvas_url"])
        valid_url = (
            url.scheme in ("http", "https")
            and url.hostname is not None
            and url.username is None
            and url.password is None
            and not url.query
            and not url.fragment
            and url.path in ("", "/")
        )
        url.port  # Reject malformed or out-of-range ports.
    except ValueError as error:
        raise ValueError(f"Invalid canvas_url: {error}") from error
    if not valid_url:
        raise ValueError("canvas_url must be an HTTP(S) origin without credentials, path, query, or fragment")
    return config


def json_text(value: dict) -> str:
    # JSON is a YAML subset, so the generator needs no YAML dependency.
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def expected_files(root: Path) -> dict[Path, str]:
    """Read and validate all sources before any generated files are written."""
    config = load_config(root)
    runtime = read_text(root / "runtime" / "run.py")
    if not runtime.strip():
        raise ValueError("runtime/run.py must not be empty")
    common = read_text(root / "prompts" / "common.md").strip()
    if not common:
        raise ValueError("prompts/common.md must not be empty")
    expected = {}
    for number, stage in enumerate(STAGES, start=1):
        prompt = read_text(root / "prompts" / f"{stage}.md").strip()
        if not prompt:
            raise ValueError(f"prompts/{stage}.md must not be empty")
        directory = Path("automations") / f"openspec-{number:02d}-{stage}"
        automation = {
            "name": f"OpenSpec {number:02d} · {stage.title()}",
            "state": "INACTIVE",
            "enabled": False,
            "trigger": {
                "type": "cron",
                "schedule": "0 0 1 1 *",
                "timezone": "Asia/Kuala_Lumpur",
            },
            "entrypoint": "python3 run.py",
            "timeout": config["timeout_seconds"],
            "keep_alive": False,
            "tarball_source": {"type": "internal"},
        }
        expected[directory / "automation.yaml"] = json_text(automation)
        expected[directory / "tarball" / "run.py"] = runtime
        expected[directory / "tarball" / "config.json"] = json_text({**config, "stage": stage})
        expected[directory / "tarball" / "prompt.md"] = f"{common}\n\n{prompt}\n"
    return expected


def build(root: Path, *, check: bool = False) -> list[Path]:
    expected = expected_files(root)
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
        print("All 7 OpenSpec bundles match their sources.")
    else:
        print(f"Built 7 OpenSpec bundles ({len(changed)} files updated).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
