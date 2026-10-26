import math
import unittest
from dataclasses import replace

from examples.review_lab.factorial import Observation, block_interval, evaluate, fixture


class FactorialContractTests(unittest.TestCase):
    def test_complementarity_is_measured_on_same_events(self):
        result = evaluate(fixture())
        self.assertLess(result["interaction"]["interval"][1], 0)
        self.assertTrue(result["descriptive_joint_evidence"])
        self.assertEqual(result["prospective_qualification"], "not_established_by_this_example")

    def test_redundant_combination_does_not_beat_retained(self):
        result = evaluate(fixture("redundant"))
        self.assertFalse(result["descriptive_joint_evidence"])
        self.assertGreater(result["interaction"]["estimate"], 0)

    def test_harmful_combination_is_preserved(self):
        result = evaluate(fixture("harmful"))
        self.assertGreater(result["joint_minus_reference"]["MARKET"]["estimate"], 0)
        self.assertFalse(result["descriptive_joint_evidence"])

    def test_row_permutations_do_not_change_result(self):
        source = fixture()
        expected = evaluate(source)
        source["AB"].reverse()
        self.assertEqual(expected, evaluate(source))

    def test_missing_arm_rejected(self):
        source = fixture(); del source["B"]
        with self.assertRaisesRegex(ValueError, "require exactly"):
            evaluate(source)

    def test_missing_event_rejected(self):
        source = fixture(); source["MARKET"].pop()
        with self.assertRaisesRegex(ValueError, "cohort mismatch"):
            evaluate(source)

    def test_duplicate_rejected(self):
        source = fixture(); source["A"].append(source["A"][0])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            evaluate(source)

    def test_inconsistent_outcome_rejected(self):
        source = fixture(); source["A"][0] = replace(source["A"][0], outcome=1)
        with self.assertRaisesRegex(ValueError, "label/block mismatch"):
            evaluate(source)

    def test_inconsistent_block_rejected(self):
        source = fixture(); source["AB"][0] = replace(source["AB"][0], block="other")
        with self.assertRaisesRegex(ValueError, "label/block mismatch"):
            evaluate(source)

    def test_unknown_outcomes_rejected(self):
        for bad in (None, True, .0, 2):
            source = fixture(); source["AB"][0] = replace(source["AB"][0], outcome=bad)
            with self.assertRaisesRegex(ValueError, "binary integers"):
                evaluate(source)

    def test_invalid_probabilities_rejected(self):
        for bad in (0, 1, -.1, 1.1, math.nan, math.inf, True, ".5"):
            source = fixture(); source["AB"][0] = replace(source["AB"][0], probability=bad)
            with self.assertRaises(ValueError):
                evaluate(source)

    def test_insufficient_blocks_never_becomes_support(self):
        source = fixture()
        source = {name: [replace(row, block="one-week") for row in rows] for name, rows in source.items()}
        result = evaluate(source)
        self.assertIsNone(result["interaction"]["interval"])
        self.assertFalse(result["descriptive_joint_evidence"])

    def test_interval_is_deterministic(self):
        self.assertEqual(evaluate(fixture()), evaluate(fixture()))

    def test_unequal_blocks_keep_event_weights(self):
        result = block_interval([0, 0, 0, 4], ["a", "a", "a", "b"], minimum_blocks=2)
        self.assertEqual(result["estimate"], 1)
        self.assertEqual(result["interval"], [0, 4])

    def test_invalid_bootstrap_inputs_rejected(self):
        for values, blocks in (([], []), ([1], []), ([math.nan], ["a"]), ([1], [""])):
            with self.assertRaises(ValueError):
                block_interval(values, blocks)

    def test_negative_interaction_alone_is_not_market_superiority(self):
        source = fixture()
        # Make MARKET decisively stronger while retaining the same negative
        # four-arm interaction. The reference comparison must still fail.
        source["MARKET"] = [replace(r, probability=.95 if r.outcome else .05) for r in source["MARKET"]]
        result = evaluate(source)
        self.assertLess(result["interaction"]["estimate"], 0)
        self.assertFalse(result["descriptive_joint_evidence"])

    def test_generic_input_is_not_claimed_to_be_invented(self):
        source = {name: [replace(r, event_id=r.event_id.replace("invented", "external")) for r in rows]
                  for name, rows in fixture().items()}
        result = evaluate(source)
        self.assertEqual(result["data_origin"], "caller_supplied_prediction_tables")
        self.assertNotIn("invented_data", result)
        self.assertNotIn("fixture_origin", result)


if __name__ == "__main__":
    unittest.main()
