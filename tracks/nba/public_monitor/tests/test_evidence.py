"""Validate the sanitized public boundary and deterministic HTML semantics."""
import copy
from html.parser import HTMLParser
import json
import unittest

from tracks.nba.public_monitor.build import EVIDENCE, OUTPUT, PROVIDERS, metric, render, validate


class PageStructure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.labels = []
        self.anchors = []
        self.th = []
        self.h1 = 0
        self.script_sources = []
        self.html_language = None
        self.live = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "html":
            self.html_language = attrs.get("lang")
        if tag == "label":
            self.labels.append(attrs.get("for"))
        if tag == "a":
            self.anchors.append(attrs.get("href"))
        if tag == "th":
            self.th.append(attrs.get("scope"))
        if tag == "h1":
            self.h1 += 1
        if tag == "script":
            self.script_sources.append(attrs.get("src"))
        if "aria-live" in attrs:
            self.live.append(attrs.get("id"))


class PublicEvidence(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EVIDENCE.read_text())

    def test_complete_capsule_validates(self):
        self.assertEqual(validate(self.data), self.data)

    def test_exact_three_cohorts_and_frozen_diagnostic_values(self):
        self.assertEqual([r["n"] for r in self.data["metrics"]], [1164, 1164, 94])
        self.assertEqual([r["correct"] for r in self.data["metrics"]], [762, 791, 61])
        self.assertAlmostEqual(self.data["metrics"][-1]["log_loss"], 0.6472265278732244, places=15)
        self.assertAlmostEqual(self.data["metrics"][-1]["brier"], 0.22903319203597727, places=15)

    def test_current_reconstruction_cannot_be_promoted_to_issued_record(self):
        self.data["current_evidence_class"] = "PROSPECTIVE_ISSUED"
        with self.assertRaisesRegex(ValueError, "boundary changed"):
            validate(self.data)

    def test_frozen_current_season_cannot_select_or_fit(self):
        for field in ("current_season_selection_allowed", "raw_source_pretip_possession_closure"):
            changed = copy.deepcopy(self.data)
            changed[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate(changed)
        self.data["latest_execution"]["current_season_fits"] = 1
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_inactive_rolling_protocol_not_silently_activated(self):
        self.data["rolling_current_protocol"] = "ACTIVE"
        with self.assertRaisesRegex(ValueError, "boundary changed"):
            validate(self.data)

    def test_historical_exposure_cannot_be_relabelled_as_unseen(self):
        self.data["historical_development_exposed"] = False
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_full_historical_branch_does_not_upgrade_failed_owner(self):
        self.data["latest_execution"]["owner_status"] = "COMPLETED"
        with self.assertRaisesRegex(ValueError, "failed owner"):
            validate(self.data)

    def test_fresh_rejected_results_cannot_widen_the_current_cohort(self):
        self.data["metrics"][-1]["n"] = 106
        with self.assertRaisesRegex(ValueError, "cohorts changed"):
            validate(self.data)

    def test_omitted_loss_cannot_be_hidden_by_changing_accuracy(self):
        self.data["metrics"][-1]["accuracy"] = 62 / 94
        with self.assertRaisesRegex(ValueError, "denominator disagree"):
            validate(self.data)

    def test_all_provider_scopes_are_required_in_stable_order(self):
        self.assertEqual([r["provider"] for r in self.data["providers"]], PROVIDERS)
        self.data["providers"].pop()
        with self.assertRaisesRegex(ValueError, "provider scopes"):
            validate(self.data)

    def test_unmatched_provider_profit_is_unknown_not_zero(self):
        self.data["providers"][0]["profit"] = 0
        with self.assertRaisesRegex(ValueError, "provider edge or profit"):
            validate(self.data)

    def test_unmatched_disagreement_accuracy_cannot_be_manufactured(self):
        self.data["providers"][1]["disagreement_accuracy"] = 0.75
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_extra_field_cannot_publish_unreviewed_payload(self):
        self.data["raw_provider_response"] = {"invented": True}
        with self.assertRaisesRegex(ValueError, "allowlisted"):
            validate(self.data)

    def test_private_operational_identifiers_are_rejected(self):
        for value in ("s3://invented-private-location/object", "/home/example/file", "a" * 64, "example.pyz"):
            changed = copy.deepcopy(self.data)
            changed["scope_note"] = value
            with self.subTest(value=value[:12]), self.assertRaisesRegex(ValueError, "private operational"):
                validate(changed)

    def test_missing_metric_stays_not_reported(self):
        self.assertEqual(metric(None), "Not reported")
        self.assertEqual(metric(0), "0.0000")

    def test_unknown_profit_does_not_become_numeric_during_render(self):
        html = render(self.data)
        self.assertEqual(html.count("<td>Unknown</td>"), 4)
        self.assertIn("Missing historical P&amp;L is unknown, not zero", html)

    def test_generated_page_matches_reviewed_evidence(self):
        self.assertEqual(OUTPUT.read_text(), render(self.data))

    def test_semantic_labels_tables_and_skip_navigation(self):
        parser = PageStructure()
        parser.feed(render(self.data))
        self.assertEqual(parser.html_language, "en")
        self.assertEqual(parser.h1, 1)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertTrue(all(scope in {"row", "col"} for scope in parser.th))
        self.assertTrue(set(parser.labels) <= set(parser.ids))
        self.assertIn("#main", parser.anchors)
        self.assertEqual(set(parser.live), {"filter-status", "demo-status", "version-status"})

    def test_no_remote_scripts_or_individual_actual_forecasts(self):
        html = render(self.data)
        parser = PageStructure()
        parser.feed(html)
        self.assertEqual(parser.script_sources, ["monitor.js"])
        self.assertNotRegex(html, r'<(?:script|img|iframe)[^>]+(?:https?:)?//')
        self.assertNotIn("<iframe", html)
        self.assertNotIn("game_id", json.dumps(self.data))

    def test_core_evidence_works_without_javascript(self):
        html = render(self.data)
        self.assertIn("<noscript>", html)
        self.assertIn('id="filters" hidden', html)
        self.assertIn('id="demo-mode" disabled', html)
        self.assertEqual(html.count('<tr data-season="'), 3)
        self.assertIn("prefers-reduced-motion:reduce", html)

    def test_three_active_families_and_separate_polymarket_products(self):
        self.assertEqual(self.data["active_provider_families"], ["DraftKings", "Kalshi", "Polymarket"])
        self.assertEqual(PROVIDERS, ["DraftKings", "Kalshi", "Polymarket US", "Polymarket international"])

    def test_prior_public_capsule_and_metrics_remain_unchanged(self):
        prior = json.loads(EVIDENCE.with_name("evidence.json").read_text())
        self.assertEqual(prior["schema"], "public.nba.monitor.v1")
        self.assertEqual(self.data["metrics"], prior["metrics"])
        self.assertEqual(len(prior["providers"]), 7)

    def test_latest_refresh_reuse_is_not_new_fit_credit(self):
        self.assertEqual(self.data["latest_refresh"]["new_estimator_fits"], 0)
        self.assertEqual(self.data["latest_refresh"]["reused_completed_historical_fits"], 366)
        self.data["latest_refresh"]["new_estimator_fits"] = 366
        with self.assertRaisesRegex(ValueError, "latest failed refresh"):
            validate(self.data)

    def test_unknown_raw_provider_history_cannot_be_reported_as_zero(self):
        self.data["providers"][0]["raw_historical_coverage"] = 0
        with self.assertRaisesRegex(ValueError, "unknown provider history"):
            validate(self.data)

    def test_both_disagreement_direction_counts_remain_unknown(self):
        for key in ("disagreement_model_right", "disagreement_provider_right"):
            changed = copy.deepcopy(self.data)
            changed["providers"][0][key] = 0
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "unknown provider history"):
                validate(changed)

    def test_new_source_version_example_is_explicitly_invented(self):
        html = render(self.data)
        self.assertIn('id="version-mode" disabled', html)
        self.assertIn("Later reconstruction (not issued)", html)
        self.assertIn("The numbers and events in this example are invented", html)


if __name__ == "__main__":
    unittest.main()
