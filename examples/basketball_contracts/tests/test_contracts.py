"""Invented-fixture contract checks; never a basketball performance benchmark."""
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta
import unittest

from examples.basketball_contracts.__main__ import walkthrough
from examples.basketball_contracts.contracts import Game, Identity, League, QuoteEvidence, ScoredForecast, SelectionPolicy, SourceEvidence, matched_brier, utc


class ContractsTests(unittest.TestCase):
    def setUp(self):
        self.event = Identity(League.NCAAM, "synthetic", "event", "one")
        self.home = Identity(League.NCAAM, "synthetic", "team", "a")
        self.away = Identity(League.NCAAM, "synthetic", "team", "b")
        self.game = Game(self.event, self.home, self.away, utc("2026-02-01T20:00:00Z"), 2025, 2026, "regular", None)
        self.cutoff = self.game.cutoff(60)

    def test_all_three_namespaces_are_distinct(self):
        ids = {str(Identity(league, "synthetic", "team", "same-native-id")) for league in League}
        self.assertEqual(len(ids), 3)
        with self.assertRaises(ValueError): Identity("wnba", "synthetic", "team", "one")

    def test_names_and_kind_do_not_replace_identity(self):
        with self.assertRaises(ValueError): Identity(League.NCAAM, "", "team", "name")
        with self.assertRaises(ValueError): Identity(League.NCAAM, "synthetic", "winner", "one")
        with self.assertRaises(ValueError): replace(self.game, home=self.event)

    def test_cross_league_game_rejected(self):
        with self.assertRaises(ValueError): replace(self.game, away=Identity(League.NCAAW, "synthetic", "team", "b"))
        with self.assertRaises(ValueError): replace(self.game, away=self.home)

    def test_seasons_and_event_type_explicit(self):
        with self.assertRaises(ValueError): replace(self.game, season_end_year=2025)
        with self.assertRaises(ValueError): replace(self.game, game_type="assume_regular")
        self.assertEqual(replace(self.game, game_type="unverified").game_type, "unverified")

    def test_unknown_neutral_is_retained(self):
        self.assertIsNone(self.game.neutral)
        with self.assertRaises(ValueError): replace(self.game, neutral="false")

    def test_date_or_naive_time_rejected(self):
        for value in ("2026-02-01", datetime(2026, 2, 1, 20)):
            with self.assertRaises(ValueError): utc(value)
        self.assertEqual(utc("2026-02-01T15:00:00-05:00"), self.game.tipoff)

    def test_horizon_fixed_before_tipoff(self):
        self.assertEqual(self.cutoff, utc("2026-02-01T19:00:00Z"))
        self.assertEqual(self.game.cutoff(1440), utc("2026-01-31T20:00:00Z"))
        with self.assertRaises(ValueError): self.game.cutoff(0)

    def test_fresh_retrieval_does_not_create_publication(self):
        source = SourceEvidence("a" * 64, utc("2026-02-02T00:00:00Z"), None, None, None)
        self.assertEqual(source.evidence_tier(self.cutoff), "inadmissible_or_unknown")
        self.assertEqual(source.evidence_tier(self.cutoff, assumed_available_at=self.cutoff), "reconstructed_research")

    def test_future_revision_prevents_strict_pit(self):
        source = SourceEvidence("a" * 64, utc("2026-02-02T00:00:00Z"),
                                utc("2026-02-01T18:00:00Z"), utc("2026-02-01T17:00:00Z"), utc("2026-02-01T19:01:00Z"))
        self.assertEqual(source.evidence_tier(self.cutoff), "inadmissible_or_unknown")
        self.assertEqual(replace(source, revised_at=utc("2026-02-01T18:00:00Z")).evidence_tier(self.cutoff), "strict_point_in_time")

    def test_forged_observation_order_rejected(self):
        with self.assertRaises(ValueError): SourceEvidence("a" * 64, self.cutoff, self.game.tipoff, None, None)
        with self.assertRaises(ValueError): SourceEvidence("not-a-hash", self.cutoff, None, None, None)

    def test_stale_and_later_quotes_rejected(self):
        q = QuoteEvidence(self.event, self.cutoff, self.cutoff, self.cutoff - timedelta(minutes=1), self.game.tipoff)
        self.assertTrue(q.eligible())
        self.assertFalse(replace(q, quote_updated_at=self.cutoff - timedelta(minutes=16)).eligible())
        self.assertFalse(replace(q, snapshot_at=self.game.tipoff).eligible())
        self.assertFalse(replace(q, quote_updated_at=self.game.tipoff).eligible())
        self.assertFalse(replace(q, label="closing_price").eligible())

    def test_historical_selection_is_separate_from_forward_monitoring(self):
        policy = SelectionPolicy(); policy.validate_fold((2022, 2023, 2024), 2025)
        policy.validate_fold((2022, 2023, 2024, 2025), 2026)
        with self.assertRaises(ValueError): policy.validate_selection((2025, 2026, 2027))
        with self.assertRaises(ValueError): policy.validate_fold((2024, 2025), 2025)
        with self.assertRaises(ValueError): policy.validate_fold((2022,), 2024)

    def test_matched_scoring_aligns_by_event_not_row_order(self):
        second = replace(self.event, native_id="two")
        a = (ScoredForecast(self.event, self.cutoff, .6, 1), ScoredForecast(second, self.cutoff, .3, 0))
        b = (ScoredForecast(second, self.cutoff, .4, 0), ScoredForecast(self.event, self.cutoff, .5, 1))
        score = matched_brier(a, b)
        self.assertEqual(score["games"], 2)
        self.assertAlmostEqual(score["synthetic_model_brier"], .125)
        self.assertAlmostEqual(score["MARKET_brier"], .205)
        self.assertIsNone(score["profit"])

    def test_cohort_horizon_target_outcome_mismatch_rejected(self):
        row = ScoredForecast(self.event, self.cutoff, .6, 1)
        for other in (replace(row, event=replace(self.event, native_id="other")),
                      replace(row, cutoff=self.game.tipoff), replace(row, target="regulation_winner"), replace(row, observed_outcome=0)):
            with self.assertRaises(ValueError): matched_brier([row], [other])
        with self.assertRaises(ValueError): matched_brier([row, row], [row])

    def test_cross_league_comparisons_not_silently_pooled(self):
        row = ScoredForecast(self.event, self.cutoff, .6, 1)
        other = replace(row, event=replace(self.event, league=League.NCAAW))
        with self.assertRaises(ValueError): matched_brier([row, other], [row, other])

    def test_invalid_probabilities_and_outcomes_rejected(self):
        for probability in (-.1, 1.1, float("nan"), float("inf")):
            with self.assertRaises(ValueError): ScoredForecast(self.event, self.cutoff, probability, 1)
        with self.assertRaises(ValueError): ScoredForecast(self.event, self.cutoff, .5, True)

    def test_identity_and_evidence_immutable(self):
        with self.assertRaises(FrozenInstanceError): self.event.native_id = "changed"

    def test_walkthrough_honest_status_and_three_tracks(self):
        report = walkthrough()
        self.assertTrue(report["synthetic_only"]); self.assertEqual(report["model_fits"], 0)
        self.assertEqual(report["owner_execution_status"], "B002_completed_reconstructed_research")
        self.assertEqual(report["previous_owner_execution_status"], "B001_failed_before_modeling")
        self.assertEqual(report["next_release"], "B003")
        self.assertEqual(report["next_owner_execution_status"], "pending")
        self.assertEqual(report["owner_real_model_fits"], 172)
        self.assertEqual(report["owner_real_forecast_rows"], 110)
        self.assertEqual(report["owner_distinct_forecast_games"], 61)
        self.assertEqual(report["owner_qualified_current_market_probabilities"], 0)
        self.assertTrue(report["example_metrics_are_not_owner_metrics"])
        self.assertIsNone(report["owner_profit"])
        self.assertIsNone(report["real_basketball_metrics"])
        self.assertEqual({x["league"] for x in report["reports"]}, {"nba", "ncaam", "ncaaw"})
        self.assertTrue(report["protected_2027_selection_rejected"])
        self.assertEqual(report["network_calls"] + report["paid_requests"] + report["orders"], 0)


if __name__ == "__main__":
    unittest.main()
