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
        self.role_config = {"workspace": "/work/demo", "spec_store": "/work/store", "store_id": "openspec-store",
                            "skill_root": "/work/demo", "profile": "codex-acp-demo", "timeout_seconds": 1800,
                            "canvas_url": "http://127.0.0.1:8000"}
        (self.root / "role-workflow.json").write_text(json.dumps(self.role_config))
        (self.root / "runtime").mkdir()
        (self.root / "runtime" / "run.py").write_text("print('fixture runtime')\n")
        (self.root / "prompts").mkdir()
        (self.root / "prompts" / "role-common.md").write_text("Role boundaries.\n")
        for stage in builder.ROLE_STAGES:
            (self.root / "prompts" / f"role-{stage}.md").write_text(f"Role {stage}.\n")

    def test_twelve_complete_bundles_bind_exact_role_and_skill(self):
        self.assertEqual(len(builder.build(self.root)), 48)
        self.assertEqual(len(list((self.root / "automations").iterdir())), 12)
        for role in builder.ROLES:
            for stage in builder.ROLE_STAGES:
                with self.subTest(role=role, stage=stage):
                    directory = self.root / "automations" / f"openspec-{role.lower()}-{stage}"
                    metadata = json.loads((directory / "automation.yaml").read_text())
                    self.assertEqual(metadata["name"], f"OpenSpec {role} · {stage.title()}")
                    self.assertEqual(metadata["trigger"], {
                        "type": "event", "source": "openspec-role-dashboard", "on": f"{stage}.requested",
                        "filter": f"schema == 'openspec-role-dashboard/v2' && stage == '{stage}' && approval == '{stage}' && role == '{role}'"})
                    self.assertEqual(json.loads((directory / "tarball/config.json").read_text()),
                                     {**self.role_config, "mode": "role", "stage": stage, "role": role})
                    self.assertEqual((directory / "tarball/prompt.md").read_text(), f"Role boundaries.\n\nRole {stage}.\n")
                    self.assertEqual((directory / "tarball/run.py").read_text(), (self.root / "runtime/run.py").read_text())
        self.assertEqual(builder.build(self.root, check=True), [])
        self.assertEqual(builder.build(self.root), [])

    def test_unexpected_definitions_fail_without_removal_or_writes(self):
        directory = self.root / "automations/openspec-role-apply"
        directory.mkdir(parents=True)
        (directory / "automation.yaml").write_text("preserve me")
        for check in (True, False):
            with self.assertRaisesRegex(ValueError, "outside automations"):
                builder.build(self.root, check=check)
            self.assertEqual((directory / "automation.yaml").read_text(), "preserve me")
            self.assertEqual(list((self.root / "automations").iterdir()), [directory])

    def test_invalid_role_configuration_writes_no_bundles(self):
        for patch in ({"workspace": "relative"}, {"spec_store": "/a/.local/b"}, {"timeout_seconds": True},
                      {"store_id": "../store"}, {"canvas_url": "https://example.com"}, {"stage": "apply"}):
            with self.subTest(patch=patch):
                (self.root / "role-workflow.json").write_text(json.dumps({**self.role_config, **patch}))
                with self.assertRaises(ValueError):
                    builder.build(self.root)
                self.assertFalse((self.root / "automations").exists())

    def test_check_reports_missing_and_stale_files_without_writing(self):
        builder.build(self.root)
        first = Path("automations/openspec-sa-propose/tarball/prompt.md")
        second = Path("automations/openspec-sa-update/tarball/run.py")
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
        (self.root / "prompts" / "role-common.md").write_text("Changed common rules.\n")
        (self.root / "prompts" / "role-apply.md").unlink()
        with self.assertRaisesRegex(ValueError, "role-apply.md"):
            builder.build(self.root)
        self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_missing_runtime_rejects_build_before_creating_outputs(self):
        (self.root / "runtime" / "run.py").unlink()
        with self.assertRaisesRegex(ValueError, "run.py"):
            builder.build(self.root)
        self.assertFalse((self.root / "automations").exists())

    def test_empty_prompt_writes_no_bundles(self):
        (self.root / "prompts/role-update.md").write_text(" ")
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            builder.build(self.root)
        self.assertFalse((self.root / "automations").exists())


if __name__ == "__main__":
    unittest.main()
