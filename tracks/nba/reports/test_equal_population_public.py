import copy
import unittest

from equal_population_public import validate_public
from project_equal_population import public_alias


def example(complete=False):
    population_hash = "a" * 64
    n = 183 if complete else 128
    model = {
        "alias": "candidate01", "label": "Basketball and market",
        "family": "Histogram gradient boosting", "feature_count": 72,
        "qualified_games": n, "missing_games": 183 - n,
        "evaluated_population_sha256": population_hash if complete else "b" * 64,
        "evidence_qualified": True, "full_population_complete": complete,
        "full_population_metrics": {"accuracy": 0.7, "brier": 0.18, "log_loss": 0.54} if complete else None,
        "diagnostic_metrics": {"accuracy": 0.7, "brier": 0.18, "log_loss": 0.54},
        "diagnostic_games": n, "blockers": [] if complete else ["MISSING_GAME_PREDICTIONS"],
    }
    return {
        "schema": "sel.nba.equal_population_dashboard.v1",
        "observed_at_utc": "2026-11-16T00:00:00Z",
        "source_receipt_sha256": "c" * 64,
        "protocol": {"validation_seasons": ["2024-25", "2025-26"],
            "test_season": "2026-27", "selection_basis": "VALIDATION_ONLY",
            "test_exposure_status": "PREVIOUSLY_EXPOSED", "automatic_promotion": False,
            "intersection_is_headline_population": False},
        "populations": [{"season": "2026-27", "phase": "regular",
            "required_games": 183, "population_verified": True,
            "population_sha256": population_hash}],
        "groups": [{"season": "2026-27", "phase": "regular", "target": "winner",
            "horizon_minutes": 120, "evidence_track": "VALID_REPLAY",
            "required_games": 183, "population_verified": True,
            "population_sha256": population_hash, "required_candidate_count": 1,
            "complete_candidate_count": int(complete), "all_required_candidates_complete": complete,
            "common_intersection_games": n, "models": [model]}],
    }


class FixedPopulationPublicTests(unittest.TestCase):
    def test_new_candidate_does_not_rename_existing_public_candidate(self):
        first = ['private-recipe-z', 'private-recipe-b']
        before = {x: public_alias(x) for x in first}
        after = {x: public_alias(x) for x in ['private-recipe-a', *first]}
        self.assertEqual(before, {x: after[x] for x in first})
        self.assertNotIn('private-recipe', ''.join(before.values()))

    def test_partial_intersection_does_not_become_season_score(self):
        value = validate_public(example())
        group = value["groups"][0]
        self.assertEqual((group["required_games"], group["common_intersection_games"]), (183, 128))
        self.assertIsNone(group["models"][0]["full_population_metrics"])
        self.assertFalse(group["all_required_candidates_complete"])

    def test_partial_score_cannot_be_labeled_full(self):
        value = example()
        model = value["groups"][0]["models"][0]
        model["full_population_metrics"] = model["diagnostic_metrics"]
        with self.assertRaisesRegex(ValueError, "Partial evidence"):
            validate_public(value)

    def test_equal_counts_with_different_membership_are_not_comparable(self):
        value = example(complete=True)
        value["groups"][0]["models"][0]["evaluated_population_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "False full-population"):
            validate_public(value)

    def test_group_cannot_reduce_fixed_denominator(self):
        value = example()
        value["groups"][0]["required_games"] = 128
        with self.assertRaisesRegex(ValueError, "fixed population"):
            validate_public(value)

    def test_zero_row_candidate_stays_required(self):
        value = example()
        group = value["groups"][0]
        missing = copy.deepcopy(group["models"][0])
        missing.update(alias="candidate02", qualified_games=0, missing_games=183,
                       evaluated_population_sha256=None, diagnostic_games=0,
                       diagnostic_metrics=None, blockers=["MODEL_BODY_UNAVAILABLE"])
        group["models"].append(missing)
        group["required_candidate_count"] = 2
        checked = validate_public(value)
        self.assertEqual(len(checked["groups"][0]["models"]), 2)
        group["required_candidate_count"] = 1
        with self.assertRaisesRegex(ValueError, "Required candidate"):
            validate_public(value)

    def test_exposed_test_cannot_be_renamed_untouched_or_used_for_selection(self):
        for key, wrong in [("test_exposure_status", "UNTOUCHED"),
                           ("selection_basis", "CURRENT_TEST_BEST")]:
            value = example()
            value["protocol"][key] = wrong
            with self.assertRaisesRegex(ValueError, "protocol"):
                validate_public(value)

    def test_private_membership_and_recipe_payloads_are_rejected(self):
        for key in ("recipe_id", "game_ids", "feature_names", "source_path"):
            value = example()
            value["groups"][0]["models"][0][key] = "private"
            with self.assertRaisesRegex(ValueError, "Private"):
                validate_public(value)

    def test_full_population_needs_valid_source_evidence_and_scores(self):
        value = example(complete=True)
        self.assertTrue(validate_public(value)["groups"][0]["all_required_candidates_complete"])
        value["groups"][0]["models"][0]["evidence_qualified"] = False
        with self.assertRaisesRegex(ValueError, "False full-population"):
            validate_public(value)

    def test_unverified_aggregate_support_is_explicitly_diagnostic(self):
        value = example()
        m = value["groups"][0]["models"][0]
        m.update(qualified_games=0, missing_games=183, evaluated_population_sha256=None,
                 evidence_qualified=False, diagnostic_evidence_status="SAVED_AGGREGATE_MEMBERSHIP_UNPROVEN")
        self.assertIsNone(validate_public(value)["groups"][0]["models"][0]["full_population_metrics"])
        del m["diagnostic_evidence_status"]
        with self.assertRaisesRegex(ValueError, "Unproved diagnostic"):
            validate_public(value)

    def test_validation_does_not_mutate_evidence(self):
        value = example()
        before = copy.deepcopy(value)
        checked = validate_public(value)
        checked["groups"][0]["models"][0]["label"] = "Changed display label"
        self.assertEqual(value, before)


if __name__ == "__main__":
    unittest.main()
