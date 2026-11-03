"""Only invented 2035 fixtures; no provider or model access."""
import unittest

from tracks.nba.public_monitor.history_panels import (
    invented_quote, inventory_view, pack_local_view, reference_panel,
    unpack_local_view, validate, walkthrough,
)


class HistoryPanels(unittest.TestCase):
    def test_late_retrieval_keeps_authentic_historical_quote(self):
        r=reference_panel([invented_quote()],"T60")[0]
        self.assertTrue(r["historical_reference_comparison_eligible"])
        self.assertFalse(r["prospective_comparison_eligible"])
        self.assertFalse(r["original_possession_before_cutoff"])

    def test_latest_and_model_cutoff_are_separate_views(self):
        a=invented_quote();b=invented_quote(quoted_at="2035-11-01T19:59:00Z",probability=.58)
        self.assertEqual(reference_panel([a,b],"T60")[0]["probability"],.61)
        self.assertEqual(reference_panel([a,b],"LATEST_BEFORE_TIP")[0]["probability"],.58)

    def test_t120_does_not_use_a_later_quote(self):
        self.assertEqual(reference_panel([invented_quote()],"T120"),[])

    def test_exact_t60_cutoff_allowed(self):
        self.assertEqual(len(reference_panel([invented_quote(quoted_at="2035-11-01T19:00:00Z")],"T60")),1)

    def test_tipoff_itself_is_not_before_tip(self):
        self.assertEqual(reference_panel([invented_quote(quoted_at="2035-11-01T20:00:00Z")],"LATEST_BEFORE_TIP"),[])

    def test_original_possession_can_qualify_prospective_reference(self):
        r=reference_panel([invented_quote(acquired_at="2035-11-01T18:59:30Z")],"T60")[0]
        self.assertTrue(r["prospective_comparison_eligible"])

    def test_unknown_settlement_keeps_price_visible(self):
        r=reference_panel([invented_quote(settlement=None)],"T60")[0]
        self.assertEqual(r["probability"],.61);self.assertFalse(r["historical_reference_comparison_eligible"])

    def test_us_and_international_are_not_pooled(self):
        rows=[invented_quote(provider="polymarket_us"),invented_quote(provider="polymarket_international")]
        self.assertEqual(len(reference_panel(rows,"T60")),2)

    def test_midpoint_and_last_trade_remain_distinct(self):
        self.assertEqual(len(reference_panel([invented_quote(),invented_quote(method="last_trade")],"T60")),2)

    def test_same_clock_conflict_is_not_resolved_by_score(self):
        with self.assertRaisesRegex(ValueError,"same-clock"):
            reference_panel([invented_quote(),invented_quote(probability=.4)],"T60")

    def test_exact_duplicate_is_reuse(self):
        self.assertEqual(len(reference_panel([invented_quote(),invented_quote()],"T60")),1)

    def test_sampled_candles_do_not_prove_latest_tick(self):
        r=reference_panel([invented_quote(tick_window_exhausted=True)],"T60")[0]
        self.assertFalse(r["latest_tick_exhaustiveness_proven"])

    def test_exhausted_tick_window_can_support_latest(self):
        r=reference_panel([invented_quote(tick_window_exhausted=True,sampling_resolution_seconds=0)],"T60")[0]
        self.assertTrue(r["latest_tick_exhaustiveness_proven"])

    def test_missing_quotes_do_not_drop_inventory_games(self):
        rows=inventory_view(["invented-game-01","invented-game-02"],reference_panel([invented_quote()],"T60"))
        self.assertEqual(len(rows),2);self.assertEqual(rows[1]["coverage"],"NOT_RECOVERED_NOT_PROOF_OF_NO_MARKET")

    def test_unjoined_game_does_not_vanish(self):
        with self.assertRaisesRegex(ValueError,"unjoined"):
            inventory_view(["another"],reference_panel([invented_quote()],"T60"))

    def test_duplicate_inventory_rejected(self):
        with self.assertRaisesRegex(ValueError,"unique"):
            inventory_view(["same","same"],[])

    def test_real_data_not_accepted_by_public_fixture_module(self):
        with self.assertRaisesRegex(ValueError,"invented"):
            validate(invented_quote(data_kind="REAL"))

    def test_unknown_fields_cannot_smuggle_outcomes_or_raw_payloads(self):
        with self.assertRaisesRegex(ValueError,"allowlisted"):
            validate(invented_quote(actual_home_win=1))

    def test_nonfinite_probability_rejected(self):
        for p in [float("nan"),float("inf"),-1,2,True]:
            with self.subTest(p=p),self.assertRaises(ValueError): validate(invented_quote(probability=p))

    def test_naive_clock_rejected(self):
        with self.assertRaisesRegex(ValueError,"timezone"):
            validate(invented_quote(acquired_at="2035-11-03T12:00:00"))

    def test_impossible_acquisition_clock_rejected(self):
        with self.assertRaisesRegex(ValueError,"predate"):
            validate(invented_quote(acquired_at="2035-11-01T17:00:00Z"))

    def test_envelope_is_integrity_not_authenticity(self):
        packed=pack_local_view(walkthrough());self.assertFalse(packed["authenticity_proven"])
        self.assertFalse(packed["upload_required"]);self.assertEqual(unpack_local_view(packed),walkthrough())

    def test_tampered_local_import_rejected(self):
        p=pack_local_view(walkthrough());p["payload_json"]=p["payload_json"].replace("0.61","0.62")
        with self.assertRaisesRegex(ValueError,"SHA-256"):unpack_local_view(p)

    def test_no_profit_or_forecast_credit_created(self):
        r=reference_panel([invented_quote()],"T60")[0]
        self.assertIsNone(r["profit"]);self.assertIsNone(r["roi"]);self.assertEqual(r["new_allocation"],0);self.assertEqual(r["new_forecast_credit"],0)

    def test_walkthrough_has_zero_real_work(self):
        d=walkthrough();self.assertEqual(d["provider_requests"],0);self.assertEqual(d["estimator_fits"],0)

    def test_output_never_mutates_source(self):
        original=invented_quote();result=reference_panel([original],"T60");result[0]["probability"]=.1
        self.assertEqual(original["probability"],.61)


if __name__ == "__main__": unittest.main()
