import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("bundle_build", Path(__file__).resolve().parents[1] / "scripts" / "build.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = {
            "workspace": "/work/demo",
            "change": "add-task-completion",
            "request": "",
            "profile": "codex-acp-demo",
            "timeout_seconds": 1800,
            "canvas_url": "http://127.0.0.1:8002",
        }
        self.write_config()
        (self.root / "runtime").mkdir()
        (self.root / "runtime" / "run.py").write_text("print('fixture runtime')\n")
        (self.root / "prompts").mkdir()
        (self.root / "prompts" / "common.md").write_text("Shared approval rules.\n")
        for stage in builder.STAGES:
            (self.root / "prompts" / f"{stage}.md").write_text(f"Run the {stage} stage.\n")

    def write_config(self):
        (self.root / "workflow.json").write_text(json.dumps(self.config))

    def test_builds_seven_complete_independent_inactive_bundles(self):
        self.assertEqual(len(builder.build(self.root)), 28)
        self.assertEqual(len(list((self.root / "automations").iterdir())), 7)
        for number, stage in enumerate(builder.STAGES, start=1):
            directory = self.root / "automations" / f"openspec-{number:02d}-{stage}"
            automation = json.loads((directory / "automation.yaml").read_text())
            self.assertEqual(automation["state"], "INACTIVE")
            self.assertFalse(automation["enabled"])
            self.assertEqual(automation["trigger"], {
                "type": "cron", "schedule": "0 0 1 1 *", "timezone": "Asia/Kuala_Lumpur"
            })
            self.assertEqual(automation["entrypoint"], "python3 run.py")
            self.assertEqual(automation["timeout"], 1800)
            self.assertEqual(automation["tarball_source"], {"type": "internal"})
            self.assertNotIn("agent_profile_id", automation)
            bundle = directory / "tarball"
            self.assertEqual(json.loads((bundle / "config.json").read_text()), {**self.config, "stage": stage})
            self.assertEqual((bundle / "run.py").read_text(), (self.root / "runtime" / "run.py").read_text())
            self.assertEqual((bundle / "prompt.md").read_text(), f"Shared approval rules.\n\nRun the {stage} stage.\n")
        self.assertEqual(builder.build(self.root, check=True), [])
        self.assertEqual(builder.build(self.root), [])

    def test_check_reports_missing_and_stale_files_without_writing(self):
        builder.build(self.root)
        first = Path("automations/openspec-01-explore/tarball/prompt.md")
        second = Path("automations/openspec-02-propose/tarball/run.py")
        (self.root / first).write_text("stale\n")
        (self.root / second).unlink()
        self.assertEqual(builder.build(self.root, check=True), [first, second])
        self.assertEqual((self.root / first).read_text(), "stale\n")
        self.assertFalse((self.root / second).exists())
        builder.build(self.root)
        self.assertEqual(builder.build(self.root, check=True), [])

    def test_missing_source_leaves_existing_bundles_untouched(self):
        builder.build(self.root)
        before = {path: path.read_bytes() for path in (self.root / "automations").rglob("*") if path.is_file()}
        (self.root / "prompts" / "common.md").write_text("Changed common rules.\n")
        (self.root / "prompts" / "archive.md").unlink()
        with self.assertRaisesRegex(ValueError, "archive.md"):
            builder.build(self.root)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_missing_runtime_rejects_build_before_creating_outputs(self):
        (self.root / "runtime" / "run.py").unlink()
        with self.assertRaisesRegex(ValueError, "run.py"):
            builder.build(self.root)
        self.assertFalse((self.root / "automations").exists())

    def test_rejects_invalid_configuration(self):
        cases = [
            ("workspace", "relative/repo"),
            ("change", "../outside"),
            ("profile", " "),
            ("request", 42),
            ("timeout_seconds", True),
            ("timeout_seconds", 0),
            ("timeout_seconds", 1860),
            ("canvas_url", "ftp://example.com"),
            ("canvas_url", "http://user:secret@example.com"),
            ("canvas_url", "http://localhost:8002/api"),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                original = self.config[field]
                self.config[field] = value
                self.write_config()
                with self.assertRaises(ValueError):
                    builder.build(self.root)
                self.assertFalse((self.root / "automations").exists())
                self.config[field] = original

    def test_rejects_unknown_configuration_fields_and_empty_prompts(self):
        self.config["profiel"] = "typo"
        self.write_config()
        with self.assertRaisesRegex(ValueError, "exactly"):
            builder.build(self.root)
        del self.config["profiel"]
        self.write_config()
        (self.root / "prompts" / "verify.md").write_text(" \n")
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            builder.build(self.root)


if __name__ == "__main__":
    unittest.main()
