"""Invented fixtures only; no credentials, provider data, model fits or I/O."""
from dataclasses import replace
import json
import unittest

from examples.fbs_contracts import interrupted_work as example


class InterruptedWorkTests(unittest.TestCase):
    def setUp(self):
        self.source = b"synthetic-source-v1"
        self.body = example.canonical([1, 2, 3])
        self.sha = example.digest(self.body)
        self.checkpoint = example.Checkpoint("u", "q", "run", example.digest(self.source),
            "2020-01-01T12:00:00Z", self.sha, ((self.sha, self.sha),), 3)
        self.kwargs = dict(run="run", source=self.source, independently_expected_source=example.digest(self.source),
            checkpoints=(self.checkpoint,), catalog_complete=True, originals={self.sha: self.body},
            replay=lambda raw: len(json.loads(raw)), assessed_at="2020-01-02T00:00:00Z")

    def test_interruption_recovers_unit_without_success_claim(self):
        result = example.recover(**self.kwargs)
        self.assertEqual(result["recovered_units"], 1)
        self.assertFalse(result["normal_owner_completion_claimed"])
        self.assertEqual(result["new_fits"], 0)

    def test_changed_source_rejected(self):
        with self.assertRaises(ValueError):
            example.recover(**{**self.kwargs, "source": b"changed"})

    def test_future_capture_rejected(self):
        self.kwargs["assessed_at"] = "2020-01-01T00:00:00Z"
        self.assertEqual(example.recover(**self.kwargs)["recovered_units"], 0)

    def test_original_clock_never_rewritten(self):
        result = example.recover(**self.kwargs)
        self.assertEqual(result["recovered"][0]["observed_at"], self.checkpoint.observed_at)

    def test_partial_catalog_cannot_hide_conflicts(self):
        result = example.recover(**{**self.kwargs, "catalog_complete": False})
        self.assertEqual(result["status"], "PARTIAL_INVENTORY_PENDING")
        self.assertEqual(result["recovered"], [])

    def test_exact_duplicate_not_double_counted(self):
        result = example.recover(**{**self.kwargs, "checkpoints": (self.checkpoint,) * 2})
        self.assertEqual(result["recovered_units"], 1)
        self.assertEqual(result["exact_duplicates"], 1)

    def test_changed_observation_clock_is_conflict_not_duplicate(self):
        newer = replace(self.checkpoint, observed_at="2020-01-01T13:00:00Z")
        result = example.recover(**{**self.kwargs, "checkpoints": (self.checkpoint, newer)})
        self.assertEqual(result["recovered_units"], 0)
        self.assertEqual(result["rejected_units"], 2)

    def test_missing_dependency_is_not_empty_success(self):
        result = example.recover(**{**self.kwargs, "originals": {}})
        self.assertEqual(result["rejected"][0]["reason"], "DEPENDENCY_ABSENT")

    def test_corrupt_dependency_is_not_reused(self):
        result = example.recover(**{**self.kwargs, "originals": {self.sha: b"changed"}})
        self.assertEqual(result["recovered_units"], 0)

    def test_complete_flag_does_not_prove_numeric_correctness(self):
        wrong = replace(self.checkpoint, result=999)
        result = example.recover(**{**self.kwargs, "checkpoints": (wrong,)})
        self.assertEqual(result["rejected"][0]["reason"], "NUMERICAL_REPLAY_DIFFERS")

    def test_incomplete_unit_not_admitted(self):
        result = example.recover(**{**self.kwargs, "checkpoints": (replace(self.checkpoint, committed=False),)})
        self.assertEqual(result["rejected"][0]["reason"], "INCOMPLETE_UNIT")

    def test_dependency_key_duplication_rejected(self):
        changed = replace(self.checkpoint, dependencies=self.checkpoint.dependencies * 2)
        result = example.recover(**{**self.kwargs, "checkpoints": (changed,)})
        self.assertEqual(result["rejected"][0]["reason"], "DEPENDENCY_CLOSURE_INVALID")

    def test_one_bad_unit_does_not_erase_other_good_unit(self):
        wrong = replace(self.checkpoint, unit="bad", request="other", result=999)
        result = example.recover(**{**self.kwargs, "checkpoints": (self.checkpoint, wrong)})
        self.assertEqual((result["recovered_units"], result["rejected_units"]), (1, 1))

    def test_active_owner_not_overridden_by_completion(self):
        p = example.ProcessIdentity("boot", 100, 200, "run")
        self.assertEqual(example.classify(p, (p,), completion_exit=0), "ACTIVE_OWNER_PRESERVED")

    def test_reused_pid_is_distinct_process(self):
        p = example.ProcessIdentity("boot", 100, 200, "run")
        q = example.ProcessIdentity("boot", 100, 300, "other")
        self.assertEqual(example.classify(p, (q,)), "INTERRUPTED_OR_ORPHANED_WITHOUT_NORMAL_COMPLETION")

    def test_boot_change_is_not_same_live_owner(self):
        p = example.ProcessIdentity("boot", 100, 200, "run")
        q = replace(p, boot="new-boot")
        self.assertEqual(example.classify(p, (q,)), "INTERRUPTED_OR_ORPHANED_WITHOUT_NORMAL_COMPLETION")

    def test_diagnostic_not_normal_completion(self):
        p = example.ProcessIdentity("boot", 100, 200, "run")
        self.assertEqual(example.classify(p, (), completion_exit=2), "FAILED_DIAGNOSTIC_COMPLETION")

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            example.clock("2020-01-01T00:00:00")

    def test_invented_demo_is_deterministic_and_zero_fit(self):
        self.assertEqual(example.invented_demo(), example.invented_demo())
        self.assertEqual(example.invented_demo()["new_fits"], 0)


if __name__ == "__main__":
    unittest.main()
