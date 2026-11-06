"""Invented failure cases; no sports data, credentials, fits or forecasts."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tracks.nba.public_monitor import checkpoint_commit
from tracks.nba.public_monitor.checkpoint_commit import run_stage, UncertainAction


class Remote:
    def __init__(self):
        self.objects = {}
        self.fail_put = False
        self.corrupt_get = False
        self.gets = 0
        self.puts = 0
    def put_create_only(self, key, raw):
        self.puts += 1
        if self.fail_put:
            raise OSError("invented unavailable storage")
        if key in self.objects and self.objects[key] != raw:
            raise ValueError("create-only conflict")
        self.objects.setdefault(key, raw)
    def get_full(self, key):
        self.gets += 1
        return b"corrupt" if self.corrupt_get else self.objects[key]


class CheckpointCommitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = Remote()
        self.calls = 0
    def action(self):
        self.calls += 1
        return {"invented_result": [1, 2, 3]}
    def run_one(self):
        return run_stage(self.root, "example", self.action, self.remote)
    def test_success_and_committed_reuse_keep_action_count_one(self):
        self.assertFalse(self.run_one()["action_reused"])
        self.assertTrue(self.run_one()["action_reused"])
        self.assertEqual((self.calls, self.remote.gets), (1, 1))
    def test_put_failure_has_no_complete_and_reuses_output(self):
        self.remote.fail_put = True
        with self.assertRaises(OSError):
            self.run_one()
        self.assertFalse((self.root / "example.commit.json").exists())
        self.remote.fail_put = False
        self.assertTrue(self.run_one()["action_reused"])
        self.assertEqual(self.calls, 1)
    def test_saved_valid_json_tampering_is_rejected_before_publication_retry(self):
        self.remote.fail_put = True
        with self.assertRaises(OSError):
            self.run_one()
        (self.root / "example.result.json").write_text('{"invented_result":[9]}')
        self.remote.fail_put = False
        with self.assertRaisesRegex(ValueError, "prepared result changed"):
            self.run_one()
        self.assertEqual((self.calls, self.remote.puts, self.remote.gets), (1, 1, 0))
        self.assertFalse((self.root / "example.commit.json").exists())
    def test_prepared_write_failure_preserves_result_and_refuses_replay(self):
        original_create = checkpoint_commit._create
        def fail_prepared(path, raw):
            if path.name.endswith(".prepared.json"):
                raise OSError("invented prepared-record capacity failure")
            return original_create(path, raw)
        with patch.object(checkpoint_commit, "_create", side_effect=fail_prepared):
            with self.assertRaises(OSError):
                self.run_one()
        self.assertTrue((self.root / "example.result.json").is_file())
        with self.assertRaisesRegex(UncertainAction, "prepared pin missing"):
            self.run_one()
        self.assertEqual((self.calls, self.remote.puts, self.remote.gets), (1, 0, 0))
    def test_missing_result_with_prepared_pin_refuses_replay(self):
        self.remote.fail_put = True
        with self.assertRaises(OSError):
            self.run_one()
        (self.root / "example.result.json").unlink()
        with self.assertRaises(UncertainAction):
            self.run_one()
        self.assertEqual(self.calls, 1)
    def test_changed_prepared_identity_is_rejected(self):
        self.remote.fail_put = True
        with self.assertRaises(OSError):
            self.run_one()
        path = self.root / "example.prepared.json"
        original = json.loads(path.read_text())
        for field, changed in (("stage", "other"), ("status", "COMPLETE"),
                               ("bytes", 0), ("result_sha256", "0" * 64)):
            with self.subTest(field=field):
                path.write_text(json.dumps(dict(original, **{field: changed})))
                with self.assertRaisesRegex(ValueError, "prepared result changed"):
                    self.run_one()
        self.assertEqual((self.calls, self.remote.puts), (1, 1))
    def test_corrupt_prepared_metadata_is_rejected(self):
        self.remote.fail_put = True
        with self.assertRaises(OSError):
            self.run_one()
        (self.root / "example.prepared.json").write_text("{")
        with self.assertRaisesRegex(ValueError, "prepared result changed"):
            self.run_one()
        self.assertEqual(self.calls, 1)
    def test_changed_intent_is_rejected_before_publication_retry(self):
        self.remote.fail_put = True
        with self.assertRaises(OSError):
            self.run_one()
        (self.root / "example.intent.json").write_text('{"stage":"other","status":"INTENT"}')
        with self.assertRaisesRegex(ValueError, "intent changed"):
            self.run_one()
        self.assertEqual((self.calls, self.remote.puts), (1, 1))
    def test_committed_reuse_requires_original_prepared_pin(self):
        self.run_one()
        (self.root / "example.prepared.json").unlink()
        with self.assertRaises(UncertainAction):
            self.run_one()
        self.assertEqual((self.calls, self.remote.gets), (1, 1))
    def test_wrong_readback_has_no_complete_and_reuses_output(self):
        self.remote.corrupt_get = True
        with self.assertRaisesRegex(ValueError, "readback"):
            self.run_one()
        self.assertFalse((self.root / "example.commit.json").exists())
        self.remote.corrupt_get = False
        self.assertTrue(self.run_one()["action_reused"])
        self.assertEqual(self.calls, 1)
    def test_encoder_failure_cannot_silently_replay_action(self):
        with self.assertRaises(ValueError):
            run_stage(self.root, "example", lambda: float("nan"), self.remote)
        with self.assertRaises(UncertainAction):
            self.run_one()
        self.assertEqual(self.calls, 0)
    def test_intent_after_hard_crash_refuses_replay(self):
        (self.root / "example.intent.json").write_text('{"stage":"example","status":"INTENT"}')
        with self.assertRaises(UncertainAction):
            self.run_one()
        self.assertEqual(self.calls, 0)
    def test_corrupt_committed_result_is_rejected(self):
        self.run_one()
        (self.root / "example.result.json").write_text('{"invented_result":[9]}')
        with self.assertRaisesRegex(ValueError, "changed"):
            self.run_one()
        self.assertEqual(self.calls, 1)
    def test_result_without_intent_is_rejected(self):
        (self.root / "example.result.json").write_text('{}')
        with self.assertRaisesRegex(ValueError, "without intent"):
            self.run_one()
    def test_unsafe_stage_name_is_rejected_before_action(self):
        with self.assertRaisesRegex(ValueError, "unsafe"):
            run_stage(self.root, "../outside", self.action, self.remote)
        self.assertEqual(self.calls, 0)
    def test_receipt_binds_stage_and_complete_status(self):
        self.run_one()
        receipt_path = self.root / "example.commit.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["stage"] = "different"
        receipt_path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "changed"):
            self.run_one()


if __name__ == "__main__":
    unittest.main()
