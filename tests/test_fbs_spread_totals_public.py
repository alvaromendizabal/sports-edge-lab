"""Invented-fixture checks for the public binary-contract presentation boundary."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "examples/fbs_contracts/spread_totals"
sys.path.insert(0, str(MODULE))
from build_board import build, probability_rank, return_rank, point_baseline_rows, validate
from render_phone_cards import render, science_sha


def fixture():
    clocks = {"generated_at": "2026-11-25T22:00:00Z", "forecast_as_of": "2026-11-25T21:00:00Z",
              "market_as_of": None, "forecast_horizon": "INVENTED TEST FIXTURE"}
    game = {"game_id": "invented-1", "home": "Home Example", "away": "Away Example",
            "kickoff_utc": "2026-11-28T22:00:00Z", "status": "scheduled", "is_current_week": True,
            "winner": {"home_probability": .67, "model": "P06", "calibration_status": "fitted_component_blend"},
            "margin": {"home_minus_away": 3.2, "model": "P03"},
            "total": {"points": 49.5, "model": "P05"}, "forecast_kind": "INVENTED_FIXTURE_ONLY",
            "forecast_as_of": clocks["forecast_as_of"], "nominal_cutoff_utc": "2026-11-28T21:00:00Z",
            "forecast_horizon": "Invented fixture", "original_issued": False}
    second = deepcopy(game)
    second.update(game_id="invented-2", home="Other Home", away="Other Away")
    base = {"contract_id": "invented-contract-1", "game_id": "invented-1", "market": "spread",
            "source": "Kalshi", "proposition": "Home Example wins by more than 7 points",
            "operator": ">", "strike": 7, "basis": "home_margin", "period": "Full game",
            "terms_summary": "Invented fixture. Includes overtime; void when fixture cancellation applies.",
            "source_url": None, "equality_settles": "NO", "settlement_status": "pending", "model": "P01",
            "forecast_as_of": clocks["forecast_as_of"], "observed_at": "2026-11-25T20:59:00Z",
            "forecast_horizon": "Invented fixture", "probability_qualified": True,
            "p_yes": .4, "p_no": .6, "integer_mass_preserved": True, "orientation_checked": True,
            "monotonicity_checked": True, "comparable_group": "invented-same-distribution",
            "most_probable_side": "NO", "primary_for_game": True, "best_return_side": "YES",
            "sides": {"YES": {"executable_price": .3, "executable_at_observation": True,
                              "observed_at": "2026-11-25T20:59:00Z", "fee_per_contract": .01,
                              "fees_qualified": True, "expected_net_per_contract": .09,
                              "return_method": "Invented fixture: one-dollar payout less price and fee"},
                      "NO": {"executable_price": .7, "executable_at_observation": True,
                             "observed_at": "2026-11-25T20:59:00Z", "fee_per_contract": .01,
                             "fees_qualified": True, "expected_net_per_contract": -.11,
                             "return_method": "Invented fixture: one-dollar payout less price and fee"}}}
    alternate = deepcopy(base)
    alternate.update(contract_id="invented-contract-2", proposition="Home Example wins by more than 10 points",
                     strike=10, p_yes=.3, p_no=.7, primary_for_game=False, sides={}, best_return_side=None)
    return {"schema": "fbs.spread-totals.public-board.v1", "owner": "fbs", "product": "Spread & Totals",
            "release": {"label": "FIXTURE", "status": "Test only", "new_model_fits": 0}, "clocks": clocks,
            "selection": {"validation_seasons": [2024, 2025], "test_season": 2026, "primary_weights": [.5, .5],
                          "test_used_for_selection": False, "training_year_reweighting": False,
                          "primary_strike_rule": "Invented fixture: predeclared first observed strike, no outcome use."},
            "population": {"manifest_games": 2, "current_week_games": 2},
            "models": {a: {"name": "Invented model", "family": "Fixture", "role": "Fixture"}
                       for a in ["P01", "P03", "P05", "P06"]},
            "games": [game, second], "contracts": [base, alternate],
            "missing_inputs": [{"game_id": "invented-2", "market": "spread", "code": "NO_OBSERVATION",
                                "detail": "Invented test fixture has no observed contract."}],
            "performance": [], "provenance": [],
            "publication": {"source_state": "Invented fixture", "deployment_state": "Not deployed",
                            "graphics_status_label": "INVENTED FIXTURE · not a forecast"}}


class PublicBoardTests(unittest.TestCase):
    def rejected(self, change, message):
        data = fixture()
        change(data)
        with self.assertRaisesRegex(ValueError, message):
            validate(data)

    def test_full_population_and_distinct_ranking_criteria(self):
        d = validate(fixture())
        self.assertEqual(len(d["games"]), 2)
        self.assertEqual(probability_rank(d, "spread")[0]["most_probable_side"], "NO")
        self.assertEqual(return_rank(d, "spread")[0]["best_return_side"], "YES")
        self.assertEqual(len(probability_rank(d, "spread")), 1)
        self.assertEqual(len(d["contracts"]), 2)

    def test_negative_zero_cannot_break_exact_json_download(self):
        self.rejected(lambda d: d["games"][0]["margin"].update(home_minus_away=-0.0), "negative zero")
        d = fixture()
        d["games"][0]["margin"]["home_minus_away"] = 0.0
        validate(d)

    def test_no_manifest_shrink(self):
        self.rejected(lambda d: d["games"].pop(), "manifest denominator")

    def test_strict_equality_reaches_no(self):
        self.rejected(lambda d: d["contracts"][0].update(equality_settles="YES"), "equality must follow")

    def test_inclusive_equality_reaches_yes(self):
        d = fixture()
        d["contracts"][0].update(operator=">=", equality_settles="YES")
        validate(d)

    def test_no_half_credit_or_noncomplementary_probabilities(self):
        self.rejected(lambda d: d["contracts"][0].update(p_no=.55), "must be complements")

    def test_adjacent_strikes_cannot_reverse_monotonicity(self):
        self.rejected(lambda d: d["contracts"][1].update(p_yes=.45, p_no=.55), "tail probability increases")

    def test_orientation_is_required(self):
        self.rejected(lambda d: d["contracts"][0].update(orientation_checked=False), "orientation and monotonicity")

    def test_total_cannot_use_team_margin_basis(self):
        self.rejected(lambda d: d["contracts"][0].update(market="total"), "orientation mismatch")

    def test_only_yes_no_are_offered(self):
        self.rejected(lambda d: d["contracts"][0].update(most_probable_side="PUSH"), "only YES or NO")

    def test_unqualified_probability_is_not_published(self):
        self.rejected(lambda d: d["contracts"][0].update(probability_qualified=False), "unqualified probability")

    def test_price_and_fees_are_required_for_net_return(self):
        self.rejected(lambda d: d["contracts"][0]["sides"]["YES"].update(fees_qualified=False), "lacks fees")
        self.rejected(lambda d: d["contracts"][0]["sides"]["YES"].update(executable_at_observation=False), "executability")

    def test_pending_or_void_is_not_a_ranked_selection(self):
        d = fixture()
        d["contracts"][0]["settlement_status"] = "void"
        self.assertEqual(probability_rank(d, "spread"), [])

    def test_exceptional_fair_price_does_not_become_a_binary_selection(self):
        d = fixture()
        d["contracts"][0]["settlement_status"] = "fair_price"
        validate(d)
        self.assertEqual(probability_rank(d, "spread"), [])
        self.assertEqual(return_rank(d, "spread"), [])

    def test_net_return_must_match_the_quoted_side_and_fee(self):
        self.rejected(lambda d: d["contracts"][0]["sides"]["YES"].update(expected_net_per_contract=.9),
                      "net return disagrees")

    def test_stale_observed_ask_is_not_executable_or_priced_profit(self):
        d = fixture()
        d["contracts"][0]["sides"]["YES"] = {
            "observed_ask_price": .3, "observed_ask_at": "2026-11-25T18:00:00Z",
            "observed_ask_status": "STALE", "executable_price": None,
            "expected_net_per_contract": None, "fees_qualified": False,
        }
        d["contracts"][0]["best_return_side"] = None
        validate(d)
        d["contracts"][0]["sides"]["YES"].update(executable_price=.3, executable_at_observation=True,
                                                       observed_at="2026-11-25T18:00:00Z")
        with self.assertRaisesRegex(ValueError, "stale or closed"):
            validate(d)

    def test_point_baseline_is_distinct_from_binary_probability(self):
        d = fixture()
        for c in d["contracts"]:
            c.update(probability_qualified=False, p_yes=None, p_no=None, most_probable_side=None,
                     gap_reason="Integer-mass fit not executed", sides={}, best_return_side=None)
        d["contracts"][0].update(point_baseline_side="NO", point_baseline_model="P03",
                                 point_baseline_value=7, point_baseline_comparison_checked=True)
        validate(d)
        self.assertEqual(probability_rank(d, "spread"), [])
        self.assertEqual(len(point_baseline_rows(d, "spread")), 1)
        with tempfile.TemporaryDirectory() as t:
            result = render(d, Path(t))
            self.assertEqual([p["kind"] for p in result["pages"]], ["all_games", "spread_point_baseline"])
        d["contracts"][0]["point_baseline_side"] = "YES"
        with self.assertRaisesRegex(ValueError, "point baseline violates"):
            validate(d)

    def test_source_coverage_preserves_denominators_and_does_not_become_a_benchmark(self):
        d = fixture()
        d["source_coverage"] = [{"provider": "The Odds API", "bookmaker": "invented_book", "season": 2026,
            "target": "margin", "horizon": "CURRENT_OBSERVATION_NOT_CANONICAL_T60",
            "observed_at": d["clocks"]["forecast_as_of"], "received_rows": 1, "qualified_rows": 1,
            "qualified_game_count": 1, "manifest_games": 2, "weekly_game_count": 1,
            "weekly_manifest_games": 2, "gap_counts": {},
            "benchmark_status": "CURRENT_REFERENCE_ONLY_NO_SCORED_COMPARISON"}]
        validate(d)
        d["source_coverage"][0]["manifest_games"] = 1
        with self.assertRaisesRegex(ValueError, "coverage denominator cannot shrink"):
            validate(d)
        d["source_coverage"][0].update(manifest_games=2, benchmark_status="HISTORICAL_PERFORMANCE")
        with self.assertRaisesRegex(ValueError, "historical scored comparison"):
            validate(d)

    def test_no_test_selection_or_training_weight_sweep(self):
        self.rejected(lambda d: d["selection"].update(test_used_for_selection=True), "test selection")
        self.rejected(lambda d: d["selection"].update(training_year_reweighting=True), "training reweighting")

    def test_prepared_2026_selected_branch_cannot_relabel_forecasts_or_credit_fits(self):
        d = fixture()
        previous = deepcopy(d["games"])
        d["release"]["next_research"] = {
            "release": "V118", "status": "PREPARED_AWAITING_OWNER_LAUNCH", "scope": ["margin", "total"],
            "training_seasons": [2024, 2025], "selection_season": 2026,
            "selection_regime": "2026_EXPOSED_VALIDATION", "prior_test_exposure_disclosed": True,
            "prospective_test": "Games after the launch-time cutoff only.",
            "forecast_snapshot_replaced": False, "new_fits_reported": 0, "new_calibrations_reported": 0,
            "campaign_summary": "Invented status fixture. No research execution.",
            "resource_policy": "Invented fixture.", "incumbent_comparison": "Same eligible observations.",
        }
        validate(d)
        self.assertEqual(d["games"], previous)
        self.assertEqual(d["selection"]["validation_seasons"], [2024, 2025])
        with tempfile.TemporaryDirectory() as t:
            rendered = render(d, Path(t))
            self.assertEqual(rendered["pages"][0]["kind"], "release_status")
            self.assertEqual(rendered["games_rendered"], 2)
        for key, value, message in [
            ("new_fits_reported", 1, "unexecuted fits"),
            ("forecast_snapshot_replaced", True, "cannot replace inherited"),
            ("prior_test_exposure_disclosed", False, "disclose prior exposure"),
        ]:
            changed = deepcopy(d)
            changed["release"]["next_research"][key] = value
            with self.assertRaisesRegex(ValueError, message):
                validate(changed)

    def test_private_path_and_model_recipe_are_rejected(self):
        self.rejected(lambda d: d["provenance"].append({"label": "s3://private/bucket"}), "private material")
        self.rejected(lambda d: d["models"]["P06"].update(feature_names=["private_transform"]), "public scope")

    def test_saved_recovery_counts_cannot_claim_finished_science(self):
        d = fixture()
        d["release"]["recovery_audit"] = {
            "qualified_base_jobs": 10, "source_blocked_base_jobs": 2, "registered_base_jobs": 12,
            "saved_base_fit_states": 4, "saved_calibration_components": 8,
            "completed_prediction_partitions": 3, "saved_states_requiring_prediction_export": 1,
            "unfinished_attempts_without_commit": 1, "remaining_base_fits_if_unchanged": 6,
            "remaining_calibrations_if_unchanged": 12, "condition": "Invented fixture; identities must match.",
            "native_release_verified": True, "native_self_test_passed": True,
            "owner_run_launched_by_preparation": False, "scientific_callbacks_changed": False,
            "new_champions_selected": False, "fixes": ["Invented operational fixture."]}
        validate(d)
        for key, value, message in [
            ("completed_prediction_partitions", 4, "prediction partitions disagree"),
            ("remaining_base_fits_if_unchanged", 7, "remaining fit denominator"),
            ("source_blocked_base_jobs", 3, "blocked and qualified budgets"),
            ("new_champions_selected", True, "cannot imply a new execution or champion"),
            ("native_self_test_passed", False, "native readiness"),
        ]:
            changed = deepcopy(d)
            changed["release"]["recovery_audit"][key] = value
            with self.assertRaisesRegex(ValueError, message):
                validate(changed)

    def test_script_payload_is_escaped_and_no_runtime_fetch_exists(self):
        d = fixture()
        d["games"][0]["home"] = "</script><script>bad()</script>"
        rendered = build(d)
        self.assertNotIn("<script>bad()", rendered)
        self.assertIn("\\u003c/script>", rendered)
        self.assertNotIn("fetch(", rendered)

    def test_served_status_requires_exact_https_site_origin(self):
        template = (MODULE / "board.html.in").read_text()
        helper = re.search(r"function publicationDisplay\(\).*?(?=\nfunction model)", template, re.S).group()
        script = "const D={publication:{site_url:'https://fbs.example.test',deployment_state:'Source preparation only'}};let window={location:{}};" + helper + "\n" + """
const cases=[
 [{protocol:'http:',origin:'http://localhost:8000'},false],
 [{protocol:'https:',origin:'https://localhost'},false],
 [{protocol:'https:',origin:'https://fbs.example.test.attacker.invalid'},false],
 [{protocol:'http:',origin:'http://fbs.example.test'},false],
 [{protocol:'https:',origin:'https://fbs.example.test'},true]
];
for(const [location,served] of cases){window.location=location;const value=publicationDisplay();if(value.includes('being served here')!==served)throw new Error('Origin status mismatch');if(value.includes('version 49'))throw new Error('Invented deployment version');}
"""
        subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)

    def test_deterministic_phone_graphics_keep_all_game_ids(self):
        d = fixture()
        with tempfile.TemporaryDirectory() as t:
            result = render(d, Path(t))
            self.assertEqual(result["games_rendered"], 2)
            game_pages = [p for p in result["pages"] if p["kind"] == "all_games"]
            self.assertEqual(game_pages[0]["game_ids"], ["invented-1", "invented-2"])
            self.assertEqual(result["science_sha256"], science_sha(d))
            self.assertEqual(len(result["pages"]), 3)
            self.assertTrue(all(p["width"] == 1290 and p["height"] == 2796 for p in result["pages"]))
            self.assertTrue(all(p["text_runs"] for p in result["pages"]))


if __name__ == "__main__":
    unittest.main()
