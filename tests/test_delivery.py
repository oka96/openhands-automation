"""Real Git fixtures for review, revision history and deterministic delivery."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
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
        for repository, name in ((self.store, "store"), (self.code, "backend")):
            repository.mkdir()
            self.git(repository, "init", "-b", "main")
            self.git(repository, "config", "user.email", "test@example.invalid")
            self.git(repository, "config", "user.name", "Workflow Test")
            self.git(repository, "remote", "add", "origin", f"https://github.com/example/{name}.git")
            (repository / "README.md").write_text("Initial\n")
            self.git(repository, "add", ".")
            self.git(repository, "commit", "-m", "Initial")
        self.config = {"spec_store": str(self.store), "workspace": str(self.code), "role": "Backend",
                       "requirement_id": "TEST-001", "spec_id": "BE-TEST-001-booking", "stage": "update",
                       "scope": {"applications": [{"repository": "https://github.com/example/backend.git"}]}}
        self.change = self.store / "openspec/changes" / self.config["spec_id"]
        self.change.mkdir(parents=True)
        (self.change / "proposal.md").write_text("Before\n")
        self.git(self.store, "add", ".")
        self.git(self.store, "commit", "-m", "Spec")

    def tearDown(self):
        self.home_patch.stop()
        self.temporary.cleanup()

    def git(self, root, *args):
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.DEVNULL).decode().strip()

    def review(self, target="code"):
        return delivery.create_review(self.config, target, str(uuid.uuid4()))

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

    def test_review_includes_added_deleted_binary_and_mode_changes(self):
        (self.code / "README.md").unlink()
        (self.code / "new.txt").write_text("New content\n")
        (self.code / "image.bin").write_bytes(b"\x00\x01")
        result = self.review()
        files = {item["path"]: item for item in result["files"]}
        self.assertEqual(files["README.md"]["status"], "deleted")
        self.assertEqual(files["new.txt"]["status"], "added")
        self.assertTrue(files["image.bin"]["binary"])
        self.assertIn("+New content", files["new.txt"]["diff"])
        self.assertEqual(result["fingerprint"], delivery.review_repository(self.config, "code")["fingerprint"])
        os.chmod(self.code / "new.txt", 0o755)
        self.assertNotEqual(result["fingerprint"], delivery.review_repository(self.config, "code")["fingerprint"])

    def test_stale_content_branch_head_origin_each_prevents_commit(self):
        for mutation in ("content", "branch", "head", "origin"):
            with self.subTest(mutation=mutation):
                (self.code / "README.md").write_text("Reviewed\n")
                review = self.review()
                if mutation == "content":
                    (self.code / "README.md").write_text("Unreviewed\n")
                elif mutation == "branch":
                    self.git(self.code, "switch", "-c", "other")
                elif mutation == "head":
                    self.git(self.code, "commit", "--allow-empty", "-m", "Another commit")
                else:
                    self.git(self.code, "remote", "set-url", "origin", "https://github.com/example/wrong.git")
                head = self.git(self.code, "rev-parse", "HEAD")
                with self.assertRaises(delivery.DeliveryError):
                    delivery.deliver(self.config, review["id"], "code", "commit", "Must not commit")
                self.assertEqual(self.git(self.code, "rev-parse", "HEAD"), head)

    def test_local_commit_has_exact_spec_files_and_preserves_unrelated_staging(self):
        (self.change / "proposal.md").write_text("Ready\n")
        (self.store / "other-spec.md").write_text("Unrelated staged work\n")
        self.git(self.store, "add", "other-spec.md")
        review = self.review("specs")
        receipt = delivery.deliver(self.config, review["id"], "specs", "commit", "Update booking contract")
        changed = self.git(self.store, "diff-tree", "--no-commit-id", "--name-only", "-r", receipt["commit"])
        self.assertEqual(changed, "openspec/changes/BE-TEST-001-booking/proposal.md")
        self.assertEqual(self.git(self.store, "diff", "--cached", "--name-only"), "other-spec.md")
        self.assertEqual(self.git(self.store, "symbolic-ref", "--short", "HEAD"), "main")
        self.assertEqual(receipt["state"], "complete")
        self.assertNotIn("url", receipt)
        self.assertEqual(delivery.deliver(self.config, review["id"], "specs", "commit", "Update booking contract"), receipt)

    def test_symlink_and_sa_code_are_rejected(self):
        (self.code / "escape").symlink_to(self.store / "README.md")
        with self.assertRaisesRegex(delivery.DeliveryError, "Linked"):
            self.review()
        config = {**self.config, "role": "SA", "spec_id": "SA-TEST-001-booking"}
        with self.assertRaisesRegex(delivery.DeliveryError, "SA"):
            delivery.create_review(config, "code", str(uuid.uuid4()))

    def test_mr_retry_after_provider_failure_reuses_commit_and_branch(self):
        (self.code / "README.md").write_text("Ready for PR\n")
        review = self.review()
        original = delivery.command
        pushes, creates = [], []
        existing = []

        def run(args, cwd, **kwargs):
            if args[:2] == ["git", "push"]:
                pushes.append(args)
                self.assertNotIn("--force", args)
                return subprocess.CompletedProcess(args, 0, b"", b"")
            if args[:3] == ["gh", "pr", "list"]:
                return subprocess.CompletedProcess(args, 0, json.dumps(existing).encode(), b"")
            if args[:3] == ["gh", "pr", "create"]:
                creates.append(args)
                self.assertIn("--body-file", args)
                if len(creates) == 1:
                    raise delivery.DeliveryError("Provider unavailable")
                return subprocess.CompletedProcess(args, 0, b"https://github.com/example/backend/pull/12\n", b"")
            return original(args, cwd, **kwargs)

        with patch.object(delivery, "command", side_effect=run):
            with self.assertRaisesRegex(delivery.DeliveryError, "Provider"):
                delivery.deliver(self.config, review["id"], "code", "merge-request", "Ship booking")
            saved = delivery.load_record(self.config, "deliveries", review["id"])
            self.assertEqual(saved["state"], "pushed")
            head = self.git(self.code, "rev-parse", "HEAD")
            receipt = delivery.deliver(self.config, review["id"], "code", "merge-request", "Ship booking")
            self.assertEqual(receipt["commit"], head)
            self.assertEqual(self.git(self.code, "rev-list", "--count", "HEAD"), "2")
            self.assertEqual(receipt["url"], "https://github.com/example/backend/pull/12")
            self.assertEqual(receipt["state"], "complete")
            delivery.deliver(self.config, review["id"], "code", "merge-request", "Ship booking")
            self.assertEqual(len(creates), 2)
            self.assertEqual(len(pushes), 2)

    def test_empty_review_cannot_commit(self):
        review = self.review()
        with self.assertRaisesRegex(delivery.DeliveryError, "no reviewed changes"):
            delivery.deliver(self.config, review["id"], "code", "commit", "Nothing")

    def test_diff_keeps_lines_distinct_without_trailing_newline(self):
        item = delivery.diff_file("README.md", {"data": b"before", "mode": "100644"}, {"data": b"after", "mode": "100644"})
        self.assertIn("-before\n\\ No newline at end of file\n+after\n", item["diff"])

    def test_changed_bytes_during_staging_never_advance_head(self):
        (self.code / "README.md").write_text("Reviewed\n")
        review = self.review()
        head = self.git(self.code, "rev-parse", "HEAD")
        original = delivery.git
        def race(root, *arguments, **kwargs):
            if arguments[0] == "add":
                (self.code / "README.md").write_text("Changed after fingerprint\n")
            return original(root, *arguments, **kwargs)
        with patch.object(delivery, "git", side_effect=race):
            with self.assertRaisesRegex(delivery.DeliveryError, "content changed"):
                delivery.deliver(self.config, review["id"], "code", "commit", "Must not substitute bytes")
        self.assertEqual(self.git(self.code, "rev-parse", "HEAD"), head)

    def test_mr_pushes_exact_reviewed_commit_and_recovers_an_existing_pr(self):
        remote = self.root / "remote.git"
        self.git(self.root, "init", "--bare", str(remote))
        (self.code / "README.md").write_text("Reviewed for delivery\n")
        review = self.review()
        original = delivery.command
        pushes = []
        def local_provider(args, cwd, **kwargs):
            if args[:2] == ["git", "push"]:
                self.assertEqual(args[2], review["origin"], "Push must use the reviewed URL, not a mutable pushurl alias")
                pushes.append(args)
                return original([*args[:2], str(remote), *args[3:]], cwd, **kwargs)
            if args[:3] == ["gh", "pr", "list"]:
                return subprocess.CompletedProcess(args, 0, b'[{"url":"https://github.com/example/backend/pull/42"}]', b"")
            self.assertNotEqual(args[:3], ["gh", "pr", "create"], "Existing PR must be reused")
            return original(args, cwd, **kwargs)
        with patch.object(delivery, "command", side_effect=local_provider):
            result = delivery.deliver(self.config, review["id"], "code", "merge-request", "Booking implementation")
        self.assertEqual(self.git(remote, "rev-parse", "refs/heads/" + result["branch"]), result["commit"])
        self.assertEqual(result["url"], "https://github.com/example/backend/pull/42")
        self.assertEqual(len(pushes), 1)
        self.assertEqual(self.git(remote, "show", result["commit"] + ":README.md"), "Reviewed for delivery")


if __name__ == "__main__":
    unittest.main()
