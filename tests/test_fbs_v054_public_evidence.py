"""Saved aggregate/display checks; no model fits or sports metric computation."""
import gzip
import json
from datetime import datetime
from pathlib import Path
import re
import unittest

DOCS=Path(__file__).resolve().parents[1]/"docs/fbs"


class PublicFbsEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=json.loads(gzip.decompress((DOCS/"current-evidence-v053.json.gz").read_bytes()))
        cls.data=json.loads(gzip.decompress((DOCS/"current-evidence-v054.json.gz").read_bytes()))
        cls.status=json.loads((DOCS/"execution-status-v054.json").read_bytes())
        cls.study=json.loads((DOCS/"learned-mixture-evaluation-v054.json").read_bytes())

    def test_every_original_game_original_issue_and_reconstruction_survives(self):
        self.assertEqual(len(self.data["games"]),2742)
        original={g["id"]:g for g in self.old["games"]}
        self.assertEqual(set(original),{g["id"] for g in self.data["games"]})
        for game in self.data["games"]:
            self.assertEqual(game["original"],original[game["id"]]["original"])
            self.assertEqual(game["historical"],original[game["id"]]["historical"])
            self.assertEqual(game["first_calibrated"],original[game["id"]]["calibrated"])

    def test_record_and_unique_game_counts_are_not_conflated(self):
        games=self.data["games"]
        self.assertEqual(sum(len(g["saved_issue_contexts"]) for g in games),500)
        self.assertEqual(sum(bool(g["saved_issue_contexts"]) for g in games),122)
        self.assertEqual(sum(g["mixture_global"]["p_home"] is not None for g in games),114)
        self.assertEqual(sum(g["mixture_gated"]["p_home"] is not None for g in games),114)
        self.assertEqual(sum(r["new_in_v053"] for g in games for r in g["saved_issue_contexts"]),256)
        self.assertEqual(self.status["new_unique_games_from_context_revisions"],0)

    def test_new_layers_preserve_temporal_order_and_do_not_backdate(self):
        stamp=lambda value:datetime.fromisoformat(value.replace("Z","+00:00"))
        for game in self.data["games"]:
            for record in game["saved_issue_contexts"]:
                times=[stamp(record[k]) for k in ("information_cutoff_utc","computed_at_utc","published_at_utc","durably_observed_at_utc","issue_deadline_utc")]
                self.assertLessEqual(times[0],times[1]);self.assertLessEqual(times[1],times[2])
                self.assertLessEqual(times[2],times[3]);self.assertLess(times[3],times[4])

    def test_actual_partial_run_and_prepared_successor_are_distinct(self):
        self.assertEqual(self.status["owner_release"],"V053")
        self.assertEqual(self.status["successful_statistical_fits"],9)
        self.assertEqual(self.status["new_base_fits"]+self.status["new_mixture_fits"],9)
        self.assertEqual(self.status["new_current_scalar_outputs"],768)
        self.assertFalse(self.status["owner_execution_success"])
        self.assertFalse(self.status["full_research_complete"])
        prepared=self.status["prepared_successor"]
        self.assertEqual(prepared["status"],"PREPARED_NOT_OWNER_EXECUTED")
        self.assertEqual(prepared["new_owner_fits"],0)
        self.assertEqual(prepared["new_owner_predictions"],0)
        self.assertTrue(prepared["registered_counts_are_not_executed_experiments"])

    def test_negative_findings_and_exposure_are_retained(self):
        self.assertEqual(self.study["games"],211)
        self.assertEqual(self.study["season"],2025)
        self.assertEqual(self.study["evidence_class"],"EXPOSED_RETROSPECTIVE_PROXY_CLOCK_RECONSTRUCTION")
        for key in ("joint_log_loss","winner_log_loss","winner_brier","margin_mae","total_mae","margin_rmse","total_rmse","margin_crps","total_crps"):
            self.assertGreater(self.study["metrics"]["gated"][key],self.study["metrics"]["foundation"][key])
            self.assertAlmostEqual(self.study["metrics"]["global"][key],self.study["metrics"]["foundation"][key],places=12)
        self.assertFalse(self.study["automatic_promotion"])
        self.assertFalse(self.study["prospective_confirmation"])

    def test_missing_coverage_does_not_turn_into_zero_probabilities(self):
        gaps=[g for g in self.data["games"] if g["season"]==2026 and g["original"]["p_home"] is None]
        self.assertEqual(len(gaps),766)
        self.assertEqual(self.status["remaining_mixture_family_views"],16)
        self.assertEqual(self.status["qualified_four_provider_baseline_games"],0)
        self.assertEqual(self.status["qualified_named_horizon_issues"],{"T1440":0,"T120":0,"T60":0})
        for game in gaps:self.assertIsNone(game["original"]["total_points"])

    def test_no_private_active_recipes_or_cloud_locations_in_new_export(self):
        forbidden={"weights","feature_names","feature_columns","model_state","saved_state","training_input_identity_sha256",
                   "forecast_record_id","s3_identity","account_id","bucket","canonical_reference"}
        def walk(value):
            if isinstance(value,dict):
                self.assertFalse(set(value)&forbidden)
                for child in value.values():walk(child)
            elif isinstance(value,list):
                for child in value:walk(child)
        walk(self.data)
        encoded=json.dumps(self.data)
        self.assertIsNone(re.search(r's3://|arn:aws:|tracks/ncaaf/|/home/sagemaker|"\d{12}"',encoded))

    def test_visible_page_has_every_layer_and_an_explicit_unexecuted_method(self):
        html=(DOCS/"current.html").read_text()
        for layer in ("original","latest_foundation","first_calibrated","calibrated","mixture_global","mixture_gated","historical"):
            self.assertIn('value="'+layer+'"',html)
        self.assertIn("No V054 owner results claimed",html)
        self.assertIn("198.39 recorded seconds",html)
        self.assertIn("129.9 min",html)
        self.assertIn("current-evidence-v054.js",html)
        self.assertTrue((DOCS/"index.html").exists())
        self.assertNotRegex(html,r'<(?:button|input|select)[^>]*(?:stake|bankroll|wager|place.bet)')

    def test_javascript_loader_carries_the_exact_downloaded_export(self):
        import base64
        loader=(DOCS/"current-evidence-v054-data.js").read_text()
        encoded=re.search(r'GZIP="([A-Za-z0-9+/=]+)"',loader).group(1)
        self.assertEqual(base64.b64decode(encoded),(DOCS/"current-evidence-v054.json.gz").read_bytes())


if __name__=="__main__":unittest.main()
