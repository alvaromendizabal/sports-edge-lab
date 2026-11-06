"""Negative-case tests for the public invented spread and ATS example."""
from dataclasses import replace
import unittest

from spread_ats import ContractError, Quote, Reference, Result, ats_record, demo, probability_at_spread


class SpreadProbabilityTests(unittest.TestCase):
    def setUp(self):
        self.ref = Reference("example", "ncaaw", "HOME", "AWAY", "Polymarket", "INTERNATIONAL", "2025-03-10T18:00:00Z", 60)
        self.quote = Quote(self.ref, "-3", "2025-03-10T16:55:00Z", "2025-03-10T16:55:01Z", "2025-03-10T16:56:00Z", True)
        self.mass = [(-7, "1/10"), (-1, "3/20"), (3, "1/5"), (4, "1/4"), (10, "3/10")]
        self.model = "2025-03-10T16:45:00Z"

    def calculate(self, **kwargs):
        args = dict(mass=self.mass, quote=self.quote, reference=self.ref, model_available_at=self.model)
        args.update(kwargs)
        return probability_at_spread(**args)

    def test_integer_spread_keeps_push_separate_from_two_complements(self):
        r = self.calculate()
        self.assertEqual(r["home"], {"cover": .55, "push": .2, "loss": .25})
        self.assertEqual(r["away"], {"cover": .25, "push": .2, "loss": .55})
        self.assertEqual(r["away_spread"], "3")
        self.assertEqual(r["home_win_probability"], .75)
        self.assertFalse(r["calibration_proved_by_this_calculation"])
        self.assertEqual(r["orders"], 0)

    def test_half_point_spread_has_no_integer_margin_push(self):
        r = self.calculate(quote=replace(self.quote, home_spread="-3.5"))
        self.assertEqual(r["home"], {"cover": .55, "push": 0., "loss": .45})
        self.assertEqual(r["away"]["cover"], .45)

    def test_receiving_points_changes_cover_without_changing_win_probability(self):
        r = self.calculate(quote=replace(self.quote, home_spread="3.5"))
        self.assertEqual(r["home"]["cover"], .9)
        self.assertEqual(r["home_win_probability"], .75)

    def test_unknown_line_never_means_pickem(self):
        for value in (None, "", "NaN", "Infinity", "-Infinity", "3.25", 3):
            with self.subTest(value=value), self.assertRaises(ContractError):
                self.calculate(quote=replace(self.quote, home_spread=value))

    def test_missing_distribution_never_uses_point_margin_or_win_probability(self):
        for mass in (None, [], [(3, "3/4")], [(3, "1/2"), (3, "1/2")], [(True, "1")], [(3.0, "1")], [(3, 1.0)], [(3, "NaN")], [(3, "-1"), (4, "2")]):
            with self.subTest(mass=mass), self.assertRaises(ContractError):
                self.calculate(mass=mass)

    def test_exact_clock_boundary_is_not_earlier(self):
        for field in ("quote_at", "source_available_at", "captured_at"):
            with self.subTest(field=field), self.assertRaises(ContractError):
                self.calculate(quote=replace(self.quote, **{field: "2025-03-10T17:00:00Z"}))
        with self.assertRaisesRegex(ContractError, "MODEL_NOT_AVAILABLE"):
            self.calculate(model_available_at="2025-03-10T17:00:00Z")

    def test_missing_clock_is_not_replaced_with_capture(self):
        for field in ("quote_at", "source_available_at", "captured_at"):
            for value in (None, "NaT", "2025-03-10T16:55:00"):
                with self.subTest(field=field, value=value), self.assertRaises(ContractError):
                    self.calculate(quote=replace(self.quote, **{field: value}))

    def test_later_capture_can_only_be_an_explicit_source_supported_reconstruction(self):
        q = replace(self.quote, captured_at="2026-03-10T17:01:00Z")
        with self.assertRaisesRegex(ContractError, "NOT_CAPTURED"):
            self.calculate(quote=q)
        r = self.calculate(quote=q, tier="SOURCE_SUPPORTED_RECONSTRUCTION")
        self.assertEqual(r["evidence_tier"], "SOURCE_SUPPORTED_RECONSTRUCTION")
        self.assertEqual(r["home"]["cover"], .55)

    def test_unverified_historical_version_rejects_both_tiers(self):
        for evidence in (False, None, "true"):
            for tier in ("CAPTURED_BEFORE_CUTOFF", "SOURCE_SUPPORTED_RECONSTRUCTION"):
                with self.subTest(evidence=evidence, tier=tier), self.assertRaisesRegex(ContractError, "UNVERIFIED"):
                    self.calculate(quote=replace(self.quote, source_version_verified=evidence), tier=tier)

    def test_reversed_clock_order_is_invalid(self):
        for fields in ({"source_available_at": "2025-03-10T16:54:00Z"}, {"captured_at": "2025-03-10T16:55:00Z"}):
            with self.subTest(fields=fields), self.assertRaisesRegex(ContractError, "CLOCK_ORDER"):
                self.calculate(quote=replace(self.quote, **fields))

    def test_game_team_gender_product_horizon_and_settlement_must_match(self):
        for fields in ({"game": "other"}, {"home": "AWAY", "away": "HOME"}, {"league": "ncaam"}, {"product": "US"}, {"horizon_minutes": 120}, {"settlement": "REGULATION_ONLY"}):
            with self.subTest(fields=fields), self.assertRaisesRegex(ContractError, "IDENTITY_MISMATCH"):
                self.calculate(reference=replace(self.ref, **fields))

    def test_unregistered_horizons_and_products_do_not_get_implicit_defaults(self):
        for fields in ({"horizon_minutes": 30}, {"horizon_minutes": True}, {"league": "nba"}, {"provider": "OTHER"}, {"provider": "DraftKings", "product": "INTERNATIONAL"}, {"settlement": "REGULATION_ONLY"}):
            ref = replace(self.ref, **fields)
            with self.subTest(fields=fields), self.assertRaises(ContractError):
                self.calculate(quote=replace(self.quote, reference=ref), reference=ref)


class ATSRecordTests(unittest.TestCase):
    def setUp(self):
        self.target = Reference("next", "ncaam", "HOME", "AWAY", "DraftKings", "US", "2025-03-10T18:00:00Z", 60)
        self.rows = []
        for day, margin in ((1, 6), (3, 1), (5, 3), (7, 8)):
            r = replace(self.target, game=f"past-{day}", tipoff=f"2025-03-{day:02d}T18:00:00Z")
            q = Quote(r, "-3", f"2025-03-{day:02d}T16:55:00Z", f"2025-03-{day:02d}T16:55:00Z", f"2025-03-{day:02d}T16:56:00Z", True)
            self.rows.append(Result(q, 70 + margin, 70, f"2025-03-{day:02d}T20:00:00Z", f"2025-03-{day:02d}T20:05:00Z"))

    def record(self, rows=None, **kwargs):
        args = dict(team="HOME", target=self.target, target_cutoff="2025-03-10T17:00:00Z")
        args.update(kwargs)
        return ats_record(self.rows if rows is None else rows, **args)

    def test_record_denominators_and_future_probability_are_separate(self):
        r = self.record()
        self.assertEqual((r["wins"], r["losses"], r["pushes"]), (2, 1, 1))
        self.assertEqual(r["settled_record_denominator"], 4)
        self.assertEqual(r["decisive_denominator"], 3)
        self.assertEqual(r["win_rate_excluding_pushes"], 2/3)
        self.assertIsNone(r["future_cover_probability"])
        self.assertIsNone(r["profit"])

    def test_away_orientation_and_venue_are_explicit(self):
        away = self.record(team="AWAY", venue="AWAY")
        self.assertEqual((away["wins"], away["losses"], away["pushes"]), (1, 2, 1))
        self.assertEqual(self.record(venue="AWAY")["settled_record_denominator"], 0)

    def test_previous_window_uses_completion_order_not_input_order(self):
        r = self.record(list(reversed(self.rows)), previous=2)
        self.assertEqual((r["wins"], r["losses"], r["pushes"]), (1, 0, 1))
        self.assertEqual(r["outside_previous_window"], 2)

    def test_missing_numeric_final_or_clock_is_an_explicit_gap(self):
        for fields in ({"home_score": None}, {"away_score": True}, {"result_available_at": None}, {"completed_at": None}, {"status": "VOID"}):
            with self.subTest(fields=fields):
                r = self.record([replace(self.rows[0], **fields)])
                self.assertEqual(r["settled_record_denominator"], 0)
                self.assertEqual(sum(r["excluded"].values()), 1)
                self.assertIsNone(r["win_rate_excluding_pushes"])

    def test_result_unknown_until_or_after_cutoff_cannot_enter_features(self):
        for stamp in ("2025-03-10T17:00:00Z", "2025-03-11T01:00:00Z"):
            r = self.record([replace(self.rows[0], result_available_at=stamp)])
            self.assertEqual(r["excluded"], {"RESULT_NOT_KNOWN_BEFORE_TARGET": 1})

    def test_target_game_is_excluded_even_with_forged_early_result(self):
        q = replace(self.rows[0].quote, reference=self.target)
        r = self.record([replace(self.rows[0], quote=q)])
        self.assertEqual(r["excluded"], {"TARGET_GAME_EXCLUDED": 1})

    def test_cross_provider_gender_product_and_horizon_are_not_pooled(self):
        for fields in ({"provider": "Kalshi"}, {"league": "ncaaw"}, {"provider": "Polymarket", "product": "INTERNATIONAL"}, {"horizon_minutes": 120}):
            row = replace(self.rows[0], quote=replace(self.rows[0].quote, reference=replace(self.rows[0].quote.reference, **fields)))
            with self.subTest(fields=fields):
                self.assertEqual(self.record([row])["excluded"], {"COHORT_CONTRACT_MISMATCH": 1})

    def test_conflicting_versions_are_quarantined_without_last_writer_wins(self):
        conflict = replace(self.rows[0], home_score=40)
        for rows in ([*self.rows, conflict], [conflict, *reversed(self.rows)]):
            r = self.record(rows)
            self.assertEqual(r["excluded"], {"CONFLICTING_GAME_VERSIONS": 2})
            self.assertEqual(r["settled_record_denominator"], 3)

    def test_identical_repeats_do_not_inflate_support(self):
        r = self.record([*self.rows, self.rows[0], self.rows[0]])
        self.assertEqual(r["exact_duplicates_collapsed"], 2)
        self.assertEqual(r["settled_record_denominator"], 4)

    def test_impossible_result_clock_is_rejected(self):
        r = self.record([replace(self.rows[0], completed_at="2025-03-01T17:00:00Z")])
        self.assertEqual(r["excluded"], {"IMPOSSIBLE_RESULT_CLOCK_ORDER": 1})

    def test_all_pushes_have_no_decisive_win_rate(self):
        r = self.record([self.rows[2]])
        self.assertEqual(r["pushes"], 1)
        self.assertEqual(r["decisive_denominator"], 0)
        self.assertIsNone(r["win_rate_excluding_pushes"])

    def test_empty_cohort_has_a_missing_rate_not_zero(self):
        r = self.record([])
        self.assertEqual(r["settled_record_denominator"], 0)
        self.assertIsNone(r["win_rate_excluding_pushes"])

    def test_cutoff_cannot_drift_after_the_registered_horizon(self):
        with self.assertRaisesRegex(ContractError, "TARGET_CUTOFF"):
            self.record(target_cutoff="2025-03-10T17:01:00Z")

    def test_demo_is_explicitly_invented_and_never_places_orders(self):
        r = demo()
        self.assertEqual(r["scope"], "INVENTED_EXAMPLE_NOT_NCAA_PERFORMANCE")
        self.assertEqual(r["record"]["excluded"], {"MISSING_CLOCK": 1})
        self.assertEqual(r["late_capture_status"], "NOT_CAPTURED_BEFORE_CUTOFF")
        self.assertEqual(r["orders"], 0)


if __name__ == "__main__":
    unittest.main()
