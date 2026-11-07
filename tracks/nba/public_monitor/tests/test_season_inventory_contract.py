"""Small synthetic contracts; no actual sports, provider or model data."""
import copy
import unittest

from season_inventory_contract import InventoryContractError, comparison_key, reconcile_season_inventory


class SeasonInventoryContractTests(unittest.TestCase):
    def setUp(self):
        self.games = [
            {"season": "current", "event_id": "event-a", "phase": "regular", "tip_at_utc": "2030-01-02T02:00:00Z"},
            {"season": "current", "event_id": "event-b", "phase": "exhibition", "status": "rescheduled"},
            {"season": "prior", "event_id": "event-c", "phase": "unresolved"},
        ]
        self.forecast = {"season": "current", "event_id": "event-a", "model_id": "fixed-recipe",
            "horizon": "T60", "evidence_kind": "retrospective", "winner_prediction": "home",
            "home_win_probability": 0.6, "home_margin": 2.0, "home_cover_probability": 0.52,
            "home_spread_line": -1.5, "total_points": 210.0}

    def test_no_prediction_or_quote_can_remove_an_official_game(self):
        result = reconcile_season_inventory(self.games, [self.forecast])
        self.assertEqual(result["displayed_events"], 3)
        self.assertEqual(result["official_events_by_season"], {"current": 2, "prior": 1})
        self.assertEqual(result["omitted_official_events"], 0)
        self.assertFalse(result["official_inventory_completeness_asserted"])
        self.assertEqual(result["board"][1]["official"]["status"], "rescheduled")
        self.assertEqual(len(result["board"][1]["missing_forecast_fields"]), 5)

    def test_input_records_and_original_clocks_are_not_mutated(self):
        before = copy.deepcopy((self.games, self.forecast))
        result = reconcile_season_inventory(self.games, [self.forecast])
        result["board"][0]["official"]["event_id"] = "changed-only-in-output"
        self.assertEqual((self.games, self.forecast), before)

    def test_null_prediction_requires_an_exact_reason(self):
        self.forecast["home_margin"] = None
        with self.assertRaises(InventoryContractError):
            reconcile_season_inventory(self.games, [self.forecast])
        self.forecast["missing_reasons"] = {"home_margin": "NO_ELIGIBLE_CAUSAL_MARGIN_MODEL"}
        result = reconcile_season_inventory(self.games, [self.forecast])
        self.assertIn("home_margin", result["board"][0]["missing_forecast_fields"])

    def test_duplicate_inventory_event_requires_explicit_reconciliation(self):
        with self.assertRaises(InventoryContractError):
            reconcile_season_inventory(self.games + [self.games[0]])

    def test_orphan_model_record_does_not_manufacture_an_official_event(self):
        self.forecast["event_id"] = "not-in-official-inventory"
        result = reconcile_season_inventory(self.games, [self.forecast])
        self.assertEqual(result["displayed_events"], 3)
        self.assertEqual(len(result["orphan_records"]["forecasts"]), 1)

    def test_us_international_archival_and_horizons_stay_separate(self):
        rows = [{"season": "current", "event_id": "event-a", "provider": provider,
                 "horizon": horizon, "product": "winner", "availability": "observed",
                 "representation": "contract_probability", "value": 0.5,
                 "acquired_at_utc": "2030-01-03T00:00:00Z", "possession_kind": "later_retrieval"}
                for provider, horizon in [("polymarket_us", "T60"),
                    ("polymarket_international", "T120"), ("market", "closing")]]
        result = reconcile_season_inventory(self.games, provider_rows=rows)["board"][0]
        self.assertEqual(len(result["providers"]), 2)
        self.assertEqual(len(result["archival_providers"]), 1)
        self.assertEqual(len(result["missing_provider_products"]), 58)

    def test_provider_refusal_is_retained_without_counting_as_observed_coverage(self):
        row = {"season": "current", "event_id": "event-a", "provider": "kalshi",
               "horizon": "opening", "product": "total", "availability": "unavailable",
               "missing_reason": "HTTP_403_ACCESS_REFUSED"}
        result = reconcile_season_inventory(self.games, provider_rows=[row])["board"][0]
        self.assertEqual(len(result["providers"]), 1)
        self.assertEqual(len(result["missing_provider_products"]), 60)
        self.assertEqual(result["providers"][0]["missing_reason"], "HTTP_403_ACCESS_REFUSED")
        gap = next(r for r in result["missing_provider_products"] if
                   (r["provider"], r["product"], r["horizon"]) == ("kalshi", "total", "opening"))
        self.assertEqual(gap["reason"], "HTTP_403_ACCESS_REFUSED")
        self.assertEqual(gap["reasons"], ["HTTP_403_ACCESS_REFUSED"])

    def test_multiple_provider_failure_reasons_are_retained(self):
        row = {"season": "current", "event_id": "event-a", "provider": "kalshi",
               "horizon": "opening", "product": "total", "availability": "unavailable",
               "missing_reason": "HTTP_403_ACCESS_REFUSED"}
        result = reconcile_season_inventory(self.games, provider_rows=[row,
            {**row, "missing_reason": "NO_OPENING_OBSERVATION_RETURNED"}, row])["board"][0]
        gap = next(r for r in result["missing_provider_products"] if
                   (r["provider"], r["product"], r["horizon"]) == ("kalshi", "total", "opening"))
        self.assertEqual(gap["reasons"], ["HTTP_403_ACCESS_REFUSED", "NO_OPENING_OBSERVATION_RETURNED"])

    def test_metadata_only_provider_row_does_not_establish_product_coverage(self):
        row = {"season": "current", "event_id": "event-a", "provider": "draftkings",
               "horizon": "T60", "product": "winner"}
        with self.assertRaises(InventoryContractError):
            reconcile_season_inventory(self.games, provider_rows=[row])

    def test_issued_horizon_requires_real_pregame_clock_and_issue_identity(self):
        self.forecast.update(evidence_kind="issued", issued_at_utc="2030-01-02T01:30:00Z", issue_hash="synthetic")
        with self.assertRaises(InventoryContractError):
            reconcile_season_inventory(self.games, [self.forecast])
        self.forecast["issued_at_utc"] = "2030-01-02T01:00:00Z"
        self.assertEqual(reconcile_season_inventory(self.games, [self.forecast])["displayed_events"], 3)

    def test_probabilities_and_line_support_are_checked(self):
        for field, value in [("home_win_probability", 1.01), ("home_margin", float("nan")),
                             ("home_spread_line", None), ("total_points", -1),
                             ("winner_prediction", ""), ("winner_prediction", True)]:
            row = {**self.forecast, field: value}
            with self.subTest(field=field), self.assertRaises(InventoryContractError):
                reconcile_season_inventory(self.games, [row])

    def test_training_cutoff_cannot_follow_origin(self):
        row = {**self.forecast, "training_cutoff_utc": "2030-01-02T01:00:01Z",
               "origin_at_utc": "2030-01-02T01:00:00Z"}
        with self.assertRaises(InventoryContractError):
            reconcile_season_inventory(self.games, [row])

    def test_exact_comparison_target_line_method_and_settlement_are_retained(self):
        row = {"season": "prior", "event_id": "event-c", "side": "home", "target": "cover_probability",
               "line": -2.5, "horizon": "T60", "product": "spread", "method": "binary_contract",
               "settlement": "includes_overtime"}
        key = comparison_key(row)
        for field, value in [("line", -3.5), ("horizon", "T120"), ("method", "point_mean"),
                             ("settlement", "regulation_only"), ("side", "away")]:
            self.assertNotEqual(key, comparison_key({**row, field: value}))

    def test_comparison_rejects_empty_dimensions(self):
        row = {"season": "prior", "event_id": "event-c", "side": "home", "target": "winner",
               "line": None, "horizon": "T60", "product": "winner", "method": "binary_contract",
               "settlement": "includes_overtime"}
        for field in ("side", "target", "horizon", "product", "method", "settlement"):
            for value in (None, "", "  "):
                with self.subTest(field=field, value=value), self.assertRaises(InventoryContractError):
                    comparison_key({**row, field: value})

    def test_contract_probabilities_cannot_be_used_as_margin_or_total_points(self):
        row = {"season": "prior", "event_id": "event-c", "side": "home", "target": "margin",
               "line": None, "horizon": "T60", "product": "point_prediction", "method": "fixed_model",
               "settlement": "includes_overtime", "representation": "point_mean"}
        self.assertEqual(comparison_key(row)[4], None)
        for target in ("margin", "total"):
            for representation in ("contract_probability", "implied_probability"):
                with self.subTest(target=target, representation=representation), self.assertRaises(InventoryContractError):
                    comparison_key({**row, "target": target, "representation": representation})
        with self.assertRaises(InventoryContractError):
            comparison_key({**row, "method": "binary_contract"})

    def test_winner_and_point_predictions_accept_only_their_explicit_none_line(self):
        row = {"season": "prior", "event_id": "event-c", "side": "home", "target": "winner",
               "line": None, "horizon": "T60", "product": "winner", "method": "binary_contract",
               "settlement": "includes_overtime"}
        self.assertIsNone(comparison_key(row)[4])
        point = {**row, "target": "total", "product": "point_prediction", "method": "fixed_model",
                 "representation": "point_mean"}
        self.assertIsNone(comparison_key(point)[4])
        with self.assertRaises(InventoryContractError):
            comparison_key({**point, "line": 210})
        without_line = dict(row); del without_line["line"]
        with self.assertRaises(InventoryContractError):
            comparison_key(without_line)


if __name__ == "__main__":
    unittest.main()
