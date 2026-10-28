"""Synthetic counterexamples for leakage and accidental historical rewriting."""
from dataclasses import replace
import unittest
from examples.basketball_contracts.feature_release import IssuedSnapshots, fixture, snapshot


class FeatureReleaseTests(unittest.TestCase):
    def setUp(self):
        self.records, self.request = fixture()

    def test_available_revisions_only_and_explicit_absence(self):
        value = snapshot(self.records, self.request)
        amber = value['features']['Amber']
        self.assertEqual(amber['prior_game_count'], 2)
        self.assertEqual(amber['rolling_points_for'], 104)
        self.assertEqual(value['excluded_counts']['not_yet_available'], 2)
        self.assertEqual(value['excluded_counts']['unverified_original_clock'], 1)

    def test_target_outcome_cannot_be_used_even_with_earlier_claimed_clock(self):
        target = replace(self.records[-1], completed_at='2024-01-07T20:00:00Z',
                         published_at='2024-01-07T21:00:00Z', observed_at='2024-01-07T22:00:00Z')
        result = snapshot(self.records[:-1] + [target], self.request)
        self.assertEqual(result['features']['Amber']['prior_game_count'], 2)
        self.assertEqual(result['excluded_counts']['target_or_future_outcome'], 1)

    def test_later_archive_does_not_change_issued_feature_identity(self):
        before = snapshot(self.records[:2] + self.records[3:4], self.request)
        later = snapshot(self.records, self.request)
        self.assertEqual(before['snapshot_sha256'], later['snapshot_sha256'])
        issued = IssuedSnapshots()
        self.assertEqual(issued.issue(before), 'issued')
        self.assertEqual(issued.issue(later), 'verified_reuse')

    def test_backdated_publication_cannot_defeat_observation_clock(self):
        record = replace(self.records[5], published_at='2024-01-08T00:00:00Z')
        result = snapshot([record], self.request)
        self.assertTrue(result['features']['Cobalt']['missing_history'])
        self.assertIsNone(result['features']['Cobalt']['rolling_points_for'])

    def test_unverified_clock_only_enters_named_research_protocol(self):
        strict = snapshot(self.records, self.request)
        research = snapshot(self.records, replace(self.request, timing='reconstructed_24h'))
        self.assertEqual(strict['features']['Amber']['prior_game_count'], 2)
        self.assertEqual(research['features']['Amber']['prior_game_count'], 3)
        self.assertEqual(research['publication_qualification'], 'research_reconstruction_only')
        self.assertNotEqual(strict['snapshot_sha256'], research['snapshot_sha256'])

    def test_twenty_four_hours_is_not_an_observation_time_override(self):
        result = snapshot([self.records[5]], replace(self.request, timing='reconstructed_24h'))
        self.assertTrue(result['features']['Cobalt']['missing_history'])

    def test_same_identity_different_revision_content_rejected(self):
        corrupted = replace(self.records[0], points_for=999)
        with self.assertRaisesRegex(ValueError, 'conflicting duplicate'):
            snapshot(self.records + [corrupted], self.request)

    def test_identical_duplicate_rows_do_not_inflate_history(self):
        before = snapshot(self.records, self.request)
        after = snapshot(self.records + self.records, self.request)
        self.assertEqual(before, after)

    def test_new_eligible_value_cannot_rewrite_issued_snapshot(self):
        changed = [replace(r, points_for=109) if r.event == 'invented-b' and r.revision == 1 else r for r in self.records]
        issued = IssuedSnapshots()
        issued.issue(snapshot(self.records, self.request))
        with self.assertRaisesRegex(ValueError, 'immutable'):
            issued.issue(snapshot(changed, self.request))

    def test_tampered_snapshot_rejected(self):
        value = snapshot(self.records, self.request)
        value['features']['Amber']['rolling_points_for'] = 999
        with self.assertRaisesRegex(ValueError, 'content does not match'):
            IssuedSnapshots().issue(value)

    def test_unordered_input_and_other_league_cannot_change_features(self):
        other = replace(self.records[0], league='ncaam', points_for=999)
        before = snapshot(self.records, self.request)
        after = snapshot(list(reversed(self.records)) + [other], self.request)
        self.assertEqual(before['snapshot_sha256'], after['snapshot_sha256'])

    def test_cutoff_and_utc_are_not_optional(self):
        for request in (replace(self.request, cutoff=self.request.tipoff),
                        replace(self.request, cutoff='2024-01-08T20:00:00')):
            with self.assertRaises(ValueError):
                snapshot(self.records, request)

    def test_observation_cannot_precede_outcome_completion(self):
        bad = replace(self.records[0], observed_at='2024-01-01T00:00:00Z')
        with self.assertRaisesRegex(ValueError, 'before completion'):
            snapshot([bad], self.request)

    def test_string_false_cannot_qualify_a_publication_clock(self):
        bad = replace(self.records[0], original_clock_verified='False')
        with self.assertRaisesRegex(ValueError, 'explicit boolean'):
            snapshot([bad], self.request)

    def test_numeric_booleans_and_noninteger_revisions_rejected(self):
        for changed in ({'points_for': True}, {'revision': True}, {'revision': 1.5}):
            with self.assertRaises(ValueError):
                snapshot([replace(self.records[0], **changed)], self.request)

    def test_identity_and_clock_types_are_validated(self):
        for changed in ({'team': 42}, {'event': ' '}, {'observed_at': None}):
            with self.assertRaises(ValueError):
                snapshot([replace(self.records[0], **changed)], self.request)


if __name__ == '__main__':
    unittest.main()
