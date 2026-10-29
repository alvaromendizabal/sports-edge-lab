import copy
from dataclasses import replace
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from examples.nba_branch import contracts as c
from examples.nba_branch.build_review import EVIDENCE, OUTPUT, render, validate


class NBAContractsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.event = c.NBAEvent("nba", "invented_provider", "game_A", 2025)
        self.observation = c.Observation(self.event, "invented_pace", 99.0,
            "2025-01-02T17:00:00Z", "2025-01-02T17:01:00Z", "2025-01-02T18:00:00Z", c.digest("raw fixture"))
        self.cutoff = "2025-01-02T19:00:00Z"
        self.job = c.registration()[0]
        self.snapshot = c.feature_snapshot(self.event, self.cutoff, [self.observation])
        self.code = c.digest("invented code identity")

    def journal(self, **changes):
        values = dict(root=self.root / "nba", experiment=self.job,
                      snapshot_sha256=self.snapshot["snapshot_sha256"], code_sha256=self.code)
        values.update(changes)
        return c.FixtureJournal(**values)

    def test_full_factorial_preserves_both_cohorts_in_every_arm(self):
        jobs = c.validate_registration(c.registration())
        self.assertEqual(len({job.identity for job in jobs}), 8)
        self.assertEqual({(job.features, job.window) for job in jobs},
                         {(f, w) for f in c.FEATURES for w in c.WINDOWS})
        for year in c.VALIDATION_SEASONS:
            self.assertEqual({job.validation_cohort_sha256 for job in jobs if job.validation_season == year},
                             {c.fixture_cohorts()[year]})

    def test_missing_comparison_arm_rejected(self):
        jobs = [job for job in c.registration() if not (job.features == "candidate" and job.window == "original")]
        with self.assertRaisesRegex(ValueError, "all four"):
            c.validate_registration(jobs)

    def test_duplicate_job_cannot_replace_missing_job(self):
        jobs = list(c.registration()); jobs[-1] = jobs[0]
        with self.assertRaises(ValueError):
            c.validate_registration(jobs)

    def test_different_validation_population_rejected(self):
        jobs = list(c.registration())
        jobs[-1] = replace(jobs[-1], validation_cohort_sha256=c.digest("different games"))
        with self.assertRaises(ValueError):
            c.validate_registration(jobs)

    def test_other_leagues_rejected_at_event_and_experiment_boundaries(self):
        for league in ("ncaam", "ncaaw", "nfl", "NBA"):
            with self.subTest(league=league):
                with self.assertRaisesRegex(ValueError, "NBA-only"):
                    replace(self.event, league=league)
                with self.assertRaisesRegex(ValueError, "NBA-only"):
                    replace(self.job, league=league)

    def test_provider_and_native_event_identity_are_not_interchangeable(self):
        self.assertNotEqual(self.event.identity, replace(self.event, provider="another_provider").identity)
        self.assertNotEqual(self.event.identity, replace(self.event, native_id="game_B").identity)
        other = replace(self.observation, event=replace(self.event, native_id="game_B"))
        with self.assertRaisesRegex(ValueError, "source event identity"):
            c.feature_snapshot(self.event, self.cutoff, [other])

    def test_current_and_future_outcomes_cannot_register_selection(self):
        for year in (2027, 2028, True):
            with self.subTest(year=year), self.assertRaisesRegex(ValueError, "current-season"):
                replace(self.job, validation_season=year)

    def test_after_cutoff_publication_rejected(self):
        late = replace(self.observation, published_at="2025-01-02T19:01:00Z",
                       first_observed_at="2025-01-02T19:02:00Z", retrieved_at="2025-01-02T20:00:00Z")
        with self.assertRaisesRegex(ValueError, "unavailable"):
            c.feature_snapshot(self.event, self.cutoff, [late])

    def test_earlier_publication_does_not_erase_late_first_observation(self):
        late = replace(self.observation, first_observed_at="2025-01-02T19:01:00Z",
                       retrieved_at="2025-01-02T20:00:00Z")
        with self.assertRaisesRegex(ValueError, "unavailable"):
            c.feature_snapshot(self.event, self.cutoff, [late])

    def test_redownload_does_not_change_original_eligibility(self):
        downloaded_later = replace(self.observation, retrieved_at="2025-02-01T20:00:00Z")
        result = c.feature_snapshot(self.event, self.cutoff, [downloaded_later])
        self.assertEqual(result["observations"][0]["first_observed_at"], self.observation.first_observed_at)
        self.assertEqual(result["observations"][0]["retrieved_at"], downloaded_later.retrieved_at)

    def test_late_revision_cannot_borrow_an_earlier_versions_clock(self):
        revision = replace(self.observation, value=105.0, content_sha256=c.digest("revised fixture"),
            published_at="2025-01-02T19:01:00Z", first_observed_at="2025-01-02T19:02:00Z",
            retrieved_at="2025-01-02T20:00:00Z")
        with self.assertRaisesRegex(ValueError, "unavailable"):
            c.feature_snapshot(self.event, self.cutoff, [revision])

    def test_unknown_timezone_or_impossible_clock_order_rejected(self):
        for value in (None, "2025-01-02T17:00:00"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                replace(self.observation, published_at=value)
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            replace(self.observation, retrieved_at="2025-01-02T16:00:00Z")

    def test_nonfinite_or_boolean_feature_is_not_an_observation(self):
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "finite"):
                replace(self.observation, value=value)

    def test_duplicate_feature_cannot_hide_a_revision(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            c.feature_snapshot(self.event, self.cutoff, [self.observation, replace(self.observation, value=101.0)])

    def test_snapshot_identity_is_order_independent_and_cutoff_bound(self):
        second = replace(self.observation, feature="invented_rest", value=2.0)
        left = c.feature_snapshot(self.event, self.cutoff, [second, self.observation])
        right = c.feature_snapshot(self.event, self.cutoff, [self.observation, second])
        self.assertEqual(left, right)
        self.assertNotEqual(left["snapshot_sha256"],
            c.feature_snapshot(self.event, "2025-01-02T19:30:00Z", [second, self.observation])["snapshot_sha256"])

    def test_exact_reentry_reuses_without_changing_accepted_bytes(self):
        journal = self.journal()
        self.assertTrue(journal.begin("probability")["work_required"])
        self.assertEqual(journal.complete("probability", b"invented estimator placeholder")["new_fixture_units"], 1)
        before = {p.relative_to(journal.root): p.read_bytes() for p in journal.root.rglob("*") if p.is_file()}
        reopened = self.journal()
        self.assertFalse(reopened.begin("probability")["work_required"])
        self.assertEqual(reopened.complete("probability", b"invented estimator placeholder")["new_fixture_units"], 0)
        self.assertEqual(reopened.counts(), {"completed_fixture_units": 1, "pending_fixture_units": 0, "real_model_fits": 0})
        after = {p.relative_to(journal.root): p.read_bytes() for p in journal.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_interrupted_start_is_not_a_completed_unit(self):
        self.journal().begin("probability")
        reopened = self.journal()
        self.assertTrue(reopened.begin("probability")["work_required"])
        self.assertEqual(reopened.counts(), {"completed_fixture_units": 0, "pending_fixture_units": 1, "real_model_fits": 0})

    def test_artifact_without_completion_recovers_without_double_counting(self):
        journal = self.journal(); journal.begin("probability")
        original = c._commit
        def interrupt_receipt(path, payload):
            if path.name == "completed.json":
                raise InterruptedError("invented interruption after artifact publication")
            return original(path, payload)
        with mock.patch.object(c, "_commit", side_effect=interrupt_receipt), self.assertRaises(InterruptedError):
            journal.complete("probability", b"invented artifact")
        self.assertEqual(self.journal().counts()["completed_fixture_units"], 0)
        self.assertEqual(self.journal().complete("probability", b"invented artifact")["new_fixture_units"], 1)
        self.assertEqual(self.journal().counts()["completed_fixture_units"], 1)

    def test_changed_artifact_is_not_reused(self):
        journal = self.journal(); start = journal.begin("probability")
        journal.complete("probability", b"original invented artifact")
        (journal.root / start["unit_id"] / "artifact.fixture").write_bytes(b"changed artifact")
        with self.assertRaisesRegex(ValueError, "content changed"):
            self.journal().begin("probability")

    def test_symlinked_checkpoint_parent_or_start_is_rejected_before_read(self):
        for redirect in ("parent", "start"):
            with self.subTest(redirect=redirect):
                journal = self.journal(root=self.root / redirect)
                unit = journal.begin("probability")["unit_id"]
                journal.complete("probability", b"invented artifact")
                path = journal.root / unit
                if redirect == "start":
                    path = path / "started.json"
                target = self.root / ("redirected-" + redirect)
                path.rename(target)
                path.symlink_to(target, target_is_directory=redirect == "parent")
                with mock.patch.object(Path, "read_text", side_effect=AssertionError("must reject before reading")):
                    with self.assertRaisesRegex(ValueError, "symlink rejected before receipt read"):
                        journal.begin("probability")

    def test_changed_window_input_or_code_cannot_adopt_same_checkpoint_root(self):
        self.journal()
        for changes in ({"experiment": replace(self.job, window="revised")},
                        {"snapshot_sha256": c.digest("changed data")}, {"code_sha256": c.digest("changed code")}):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, "immutable"):
                self.journal(**changes)

    def test_pending_receipt_mutation_is_rejected(self):
        journal = self.journal(); unit = journal.begin("probability")["unit_id"]
        path = journal.root / unit / "started.json"
        changed = json.loads(path.read_text()); changed["state"] = "completed"
        path.write_bytes(c.canonical(changed))
        with self.assertRaisesRegex(ValueError, "identity changed"):
            self.journal().counts()

    def test_distinct_components_are_counted_once_each(self):
        journal = self.journal()
        for slot in ("probability", "margin"):
            journal.begin(slot); journal.complete(slot, b"invented component artifact")
            journal.begin(slot)
        self.assertEqual(journal.counts()["completed_fixture_units"], 2)
        self.assertEqual(journal.counts()["real_model_fits"], 0)

    def test_shared_raw_bytes_remain_unchanged_during_branch_derivation(self):
        source = self.root / "shared.json"; source.write_bytes(b'{"invented_value":4}')
        before = source.stat(); pin = hashlib.sha256(source.read_bytes()).hexdigest()
        raw = c.read_shared_source(source, pin)
        derived = json.loads(raw); derived["invented_value"] = 5
        (self.root / "nba-derived.json").write_text(json.dumps(derived))
        self.assertEqual(c.read_shared_source(source, pin), raw)
        self.assertEqual(source.stat().st_mtime_ns, before.st_mtime_ns)

    def test_shared_hash_change_and_symlink_are_rejected(self):
        source = self.root / "shared.json"; source.write_bytes(b"invented bytes")
        with self.assertRaisesRegex(ValueError, "content changed"):
            c.read_shared_source(source, c.digest("unrelated"))
        link = self.root / "alias.json"; link.symlink_to(source)
        with self.assertRaisesRegex(ValueError, "immutable reference"):
            c.read_shared_source(link, hashlib.sha256(source.read_bytes()).hexdigest())

    def test_walkthrough_is_offline_invented_and_has_zero_new_work_on_reentry(self):
        with mock.patch("socket.socket.connect", side_effect=AssertionError("network forbidden")):
            result = c.walkthrough()
        self.assertEqual(result["registered_jobs"], 8)
        self.assertFalse(result["reentry"]["work_required"])
        self.assertEqual(result["actual_model_fits"], 0)
        self.assertEqual(result["network_requests"], 0)
        self.assertFalse(result["owner_execution_proved"])


class PublicEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EVIDENCE.read_text())

    def test_unique_nba_lineage_is_separate_from_combined_total(self):
        data = validate(self.data)
        self.assertEqual(sum(row["new_unique_units"] for row in data["nba_lineage"]), 85)
        self.assertEqual(data["new_real_nba_units"], 10)
        self.assertEqual(data["combined_basketball_units"], 268)

    def test_double_counted_lineage_and_changed_scope_rejected(self):
        bad = copy.deepcopy(self.data); bad["nba_lineage"].append(bad["nba_lineage"][0])
        with self.assertRaisesRegex(ValueError, "duplicate release"):
            validate(bad)
        bad = copy.deepcopy(self.data); bad["lifetime_nba_units"] = bad["combined_basketball_units"]
        with self.assertRaises(ValueError):
            validate(bad)

    def test_pending_research_promotion_and_current_selection_cannot_be_inflated(self):
        for key, value in (("B010_NBA_real_execution", "completed"), ("nba_challenger_promoted", True),
                           ("qualified_market_advantage", True), ("current_season_selection_allowed", True),
                           ("owner_status", "SUCCESS_WITHOUT_GAPS")):
            bad = copy.deepcopy(self.data); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(bad)

    def test_editorial_rating_is_not_a_predictive_result(self):
        bad = copy.deepcopy(self.data); bad["portfolio_rating"]["after"] = 9.9
        with self.assertRaisesRegex(ValueError, "editorial rating"):
            validate(bad)

    def test_committed_standalone_review_matches_evidence_and_local_navigation(self):
        html = render(self.data)
        self.assertEqual(OUTPUT.read_text(), html)
        self.assertIn("B010 real execution pending", html)
        self.assertIn("235 basketball scorecards and 120 overlap specifications", html)
        self.assertNotIn("<script", html)
        class Links(HTMLParser):
            def __init__(self):
                super().__init__(); self.targets = []; self.headings = 0
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "a": self.targets.append(attrs["href"])
                if tag == "h1": self.headings += 1
        parser = Links(); parser.feed(html)
        self.assertEqual(parser.headings, 1)
        for target in parser.targets:
            # Full repository navigation is additionally checked by the existing hygiene workflow.
            self.assertFalse(target.startswith(("http:", "https:", "//")))
            self.assertFalse("?" in target)


if __name__ == "__main__":
    unittest.main()
