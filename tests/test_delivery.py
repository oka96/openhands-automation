"""Revision history remains readable after automated Git delivery is retired."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid


spec = importlib.util.spec_from_file_location("delivery", Path(__file__).resolve().parents[1] / "runtime/delivery.py")
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.home = self.root / "home"
        self.home.mkdir()
        self.home_patch = patch.object(Path, "home", return_value=self.home)
        self.home_patch.start()
        self.store, self.code = self.root / "store", self.root / "code"
        self.store.mkdir()
        self.code.mkdir()
        self.config = {"spec_store": str(self.store), "workspace": str(self.code), "role": "Backend",
                       "requirement_id": "TEST-001", "spec_id": "BE-TEST-001-booking", "stage": "update",
                       "scope": {"applications": [{"repository": "https://github.com/example/backend.git"}]}}
        self.change = self.store / "openspec/changes" / self.config["spec_id"]
        self.change.mkdir(parents=True)
        (self.change / "proposal.md").write_text("Before\n")

    def tearDown(self):
        self.home_patch.stop()
        self.temporary.cleanup()

    def test_successive_revisions_and_partial_failure_are_distinct(self):
        before = delivery.spec_snapshot(self.config)
        (self.change / "proposal.md").write_text("First update\n")
        first = delivery.save_revision(self.config, before, "completed", str(uuid.uuid4()))
        before = delivery.spec_snapshot(self.config)
        (self.change / "proposal.md").write_text("Partial second update\n")
        second = delivery.save_revision(self.config, before, "execution_error", str(uuid.uuid4()))
        self.assertNotEqual(first["id"], second["id"])
        self.assertIn("-Before", first["files"][0]["diff"])
        self.assertIn("-First update", second["files"][0]["diff"])
        self.assertEqual([item["outcome"] for item in delivery.history(self.config)["revisions"]], ["execution_error", "completed"])
        self.assertEqual(delivery.load_record(self.config, "revisions", first["id"]), first)
        self.assertIsNone(delivery.save_revision(self.config, delivery.spec_snapshot(self.config), "completed", str(uuid.uuid4())))

    def test_cross_role_and_store_history_is_inaccessible(self):
        before = delivery.spec_snapshot(self.config)
        (self.change / "proposal.md").write_text("Changed\n")
        saved = delivery.save_revision(self.config, before, "completed", str(uuid.uuid4()))
        for context in ({**self.config, "role": "Frontend", "spec_id": "FE-TEST-001-booking"},
                        {**self.config, "spec_store": str(self.code)}):
            self.assertEqual(delivery.history(context)["revisions"], [])
            with self.assertRaises(delivery.DeliveryError):
                delivery.load_record(context, "revisions", saved["id"])


    def test_old_review_and_delivery_records_remain_readable(self):
        for kind in ('reviews', 'deliveries'):
            record = {'id': str(uuid.uuid4()), 'context': delivery.identity(self.config),
                      'created_at': delivery.now(), 'files': [], 'stage': 'commit'}
            delivery.save_record(self.config, kind, record)
            self.assertEqual(delivery.load_record(self.config, kind, record['id']), record)
            self.assertEqual(delivery.history(self.config)[kind][0]['id'], record['id'])

    def test_spec_snapshot_rejects_links_and_preserves_added_deleted_binary_files(self):
        before = delivery.spec_snapshot(self.config)
        (self.change / 'proposal.md').unlink()
        (self.change / 'image.bin').write_bytes(b'\x00binary')
        record = delivery.save_revision(self.config, before, 'completed', str(uuid.uuid4()))
        files = {Path(item['path']).name: item for item in record['files']}
        self.assertEqual(files['proposal.md']['status'], 'deleted')
        self.assertTrue(files['image.bin']['binary'])
        (self.change / 'linked.md').symlink_to(self.code)
        with self.assertRaises(delivery.DeliveryError):
            delivery.spec_snapshot(self.config)

    def test_diff_keeps_lines_distinct_without_trailing_newline(self):
        item = delivery.diff_file("README.md", {"data": b"before", "mode": "100644"}, {"data": b"after", "mode": "100644"})
        self.assertIn("-before\n\\ No newline at end of file\n+after\n", item["diff"])


if __name__ == "__main__":
    unittest.main()
