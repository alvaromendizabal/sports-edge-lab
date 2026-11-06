"""Every quantity and identity in these tests is invented."""
from dataclasses import replace
import unittest

from tracks.nba.public_monitor.phase_storage import (
    Volume, WorkspaceBinding, admit_next_write, choose_volume, validate_resume,
)


class PhaseStorageTests(unittest.TestCase):
    def plan(self, home, candidates=(), **kwargs):
        return choose_volume(home, candidates,
            phase_peaks={"prepare": 800, "restore": 3000, "report": 3400},
            return_reserve=300, work_reserve=200, **kwargs)

    def test_fixed_threshold_can_accept_an_insufficient_phase_peak(self):
        home = Volume("home", "fictional-volume-a", 3200)
        self.assertGreater(home.free_bytes, 2000)  # Illustrative fixed threshold.
        self.assertFalse(self.plan(home)["admitted"])

    def test_independent_adequate_volume_can_support_work(self):
        home = Volume("home", "fictional-volume-a", 3200)
        alternate = Volume("scratch", "fictional-volume-b", 5000)
        result = self.plan(home, [alternate])
        self.assertTrue(result["admitted"])
        self.assertEqual(result["selected"], "scratch")
        self.assertFalse(result["capacity_is_reserved"])

    def test_same_device_never_sums_or_borrows_capacity(self):
        home = Volume("home", "fictional-volume-a", 3200)
        alias = Volume("another-label", "fictional-volume-a", 5000)
        result = self.plan(home, [alias])
        self.assertFalse(result["admitted"])
        self.assertEqual(result["observations"][1]["usable_bytes"], 3200)
        self.assertIn("SHARED_DEVICE_ADDS_NO_CAPACITY", result["observations"][1]["reasons"])

    def test_home_return_capacity_remains_required_with_separate_work_volume(self):
        result = self.plan(Volume("home", "a", 299), [Volume("scratch", "b", 10000)])
        self.assertFalse(result["admitted"])
        self.assertIn("RETURN_RESERVE_UNAVAILABLE", result["observations"][1]["reasons"])

    def test_sufficient_home_keeps_return_and_work_reserves(self):
        result = self.plan(Volume("home", "a", 3900))
        self.assertTrue(result["admitted"])
        self.assertEqual(result["observations"][0]["required_bytes"], 3900)

    def test_unwritable_home_cannot_be_rescued_by_separate_work_volume(self):
        home = Volume("home", "a", 3200, writable=False)
        result = self.plan(home, [Volume("scratch", "b", 10000)])
        self.assertFalse(result["admitted"])
        self.assertIn("HOME_RETURN_VOLUME_UNAVAILABLE", result["observations"][1]["reasons"])

    def test_readonly_and_memory_backed_alternatives_are_rejected(self):
        home = Volume("home", "a", 3200)
        for alternate in (Volume("scratch", "b", 5000, writable=False),
                          Volume("scratch", "b", 5000, memory_backed=True)):
            with self.subTest(alternate=alternate):
                self.assertFalse(self.plan(home, [alternate])["admitted"])

    def test_cumulative_sparse_files_are_budgeted_before_next_allocation(self):
        self.assertTrue(admit_next_write(1000, next_file_bytes=500, unfilled_sparse_bytes=0, reserve_bytes=200))
        self.assertFalse(admit_next_write(1000, next_file_bytes=500, unfilled_sparse_bytes=400, reserve_bytes=200))

    def test_invalid_byte_quantities_are_rejected(self):
        for invalid in (-1, True, 1.5):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                Volume("home", "a", invalid)


class WorkspaceResumeTests(unittest.TestCase):
    def setUp(self):
        self.binding = WorkspaceBinding("nba", "fictional-build", "fictional-workspace",
                                        "fictional-volume", "fictional-principal")

    def validate(self, observed=None, **kwargs):
        options = dict(exists=True, is_symlink=False, private_permissions=True)
        options.update(kwargs)
        return validate_resume(self.binding, observed or self.binding, **options)

    def test_same_private_binding_resumes(self):
        self.assertTrue(self.validate()["binding_valid"])
        self.assertFalse(self.validate()["silent_fallback_permitted"])

    def test_missing_workspace_requires_recovery(self):
        with self.assertRaisesRegex(ValueError, "recovery"):
            self.validate(exists=False)

    def test_replaced_volume_workspace_build_or_principal_is_rejected(self):
        for field in ("build", "workspace", "device", "principal"):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "binding changed"):
                self.validate(replace(self.binding, **{field: "different-fictional-value"}))

    def test_symlink_or_nonprivate_permissions_is_rejected(self):
        for option in ({"is_symlink": True}, {"private_permissions": False}):
            with self.subTest(option=option), self.assertRaises(ValueError):
                self.validate(**option)
