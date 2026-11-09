"""Regression contracts for dated partials, complete grids and public boundaries."""
import base64
import copy
import gzip
import json
import re
import unittest

from build_season_review_n054 import HERE, build, load, validate


class PublicN061(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load(HERE/'public_projection_n061.json.gz')

    def rejected(self, mutate):
        value = copy.deepcopy(self.data)
        mutate(value)
        with self.assertRaises(ValueError):
            validate(value)

    def test_actual_partial_counts_and_original_nulls(self):
        owner = self.data['n061_owner_status']
        self.assertEqual((owner['native_states'],owner['meta_states'],owner['issue_rows']),(27,0,2294))
        self.assertIsNone(owner['aggregate_fit_total'])
        self.assertIsNone(owner['aggregate_issue_total'])
        self.assertEqual(owner['monitor_evaluations'],0)

    def test_schedule_and_new_equal_grids(self):
        snapshot = self.data['snapshot']
        self.assertEqual((snapshot['completed'],snapshot['in_progress'],snapshot['halftime'],snapshot['scheduled']),(134,1,0,137))
        self.assertEqual(sum(len(row['horizons']) for game in self.data['games'] for row in game['source_coverage']),53856)
        self.assertEqual(self.data['counts']['private_model_cells'],115056)

    def test_original_metrics_and_source_prefixes_unchanged(self):
        old = json.load(gzip.open(HERE/'public_projection_n060.json.gz','rt'))
        self.assertEqual(self.data['scoreboards'][:1214],old['scoreboards'])
        self.assertEqual(self.data['distribution_scoreboards'],old['distribution_scoreboards'])
        self.assertEqual(self.data['cohorts'][:len(old['cohorts'])],old['cohorts'])
        for current, previous in zip(self.data['games'],old['games'],strict=True):
            self.assertEqual(current['game_id'],previous['game_id'])
            for current_row, previous_row in zip(current['source_coverage'],previous['source_coverage'],strict=True):
                self.assertEqual(current_row['horizons'][:19],previous_row['horizons'])

    def test_new_scoreboard_identities_are_unique_and_separate(self):
        rows = self.data['scoreboards']
        self.assertEqual(len(rows),1289)
        # Original dated provider rows remain byte-for-byte compatible, including
        # their original repetitions across matched cohorts. New results must
        # not collapse those rows or overwrite a previous result identity.
        identity = lambda row: (row['public_model_id'],row['study'],row['season'],row['target'],row['horizon'])
        identities = [identity(row) for row in rows[1214:]]
        self.assertEqual(len(identities),75)
        self.assertEqual(len(identities),len(set(identities)))
        self.assertTrue(set(identities).isdisjoint(identity(row) for row in rows[:1214]))

    def test_actual_monitor_failure_populations_sum_exactly(self):
        owner = self.data['n061_owner_status']
        values = [owner[key] for key in ('monitor_supported_pointer_repair_rows','monitor_conditional_identity_rows','monitor_other_unsupported_rows','monitor_not_final_rows')]
        self.assertEqual(values,[345,108,13,4620])
        self.assertEqual(sum(values),5086)

    def test_five_provider_statuses_without_invented_comparisons(self):
        rows = self.data['provider_capabilities']
        self.assertEqual(len(rows),5)
        for row in rows:
            if row['provider'] in {'PrizePicks','Underdog'}:
                self.assertEqual(row['status'],'NO_ADMITTED_COMPARABLE_GAME_LEVEL_SOURCE_IN_THIS_RETURN')
        self.assertTrue(all(len(game['source_coverage'])==9 for game in self.data['games']))

    def test_prepared_feature_counts_have_zero_actual_credit(self):
        counts = self.data['v5_scope']['candidate_counts']
        self.assertEqual((counts['inherited_proposed'],counts['inherited_implemented'],counts['inherited_blocked']),(245,193,52))
        self.assertEqual((counts['new_proposed'],counts['new_implemented'],counts['new_blocked']),(10,10,0))
        self.assertTrue(all(counts[key]==0 for key in ('owner_materialized','owner_admitted','owner_evaluated','owner_promoted')))

    def test_current_render_exactly_matches_payload(self):
        body = (HERE/'season_review_n061.html').read_text()
        self.assertEqual(body,build(self.data))
        raw = re.search(r'<script id="nfl-public-payload"[^>]*>([^<]+)</script>',body)[1]
        self.assertEqual(json.loads(gzip.decompress(base64.b64decode(raw))),self.data)
        self.assertIn('N060 retained 2,294 issued rows',body)
        self.assertIn('id="provider-capabilities"',body)

    def test_original_failure_relabel_rejected(self):
        self.rejected(lambda d:d['n061_owner_status'].update(status='COMPLETE'))

    def test_null_repair_rejected(self):
        self.rejected(lambda d:d['n061_owner_status'].update(aggregate_fit_total=27))

    def test_false_monitor_success_rejected(self):
        self.rejected(lambda d:d['n061_owner_status'].update(monitor_evaluations=345))

    def test_conditional_rows_not_reclassified_as_supported(self):
        self.rejected(lambda d:d['n061_owner_status'].update(monitor_supported_pointer_repair_rows=453))

    def test_invented_V5_fit_rejected(self):
        self.rejected(lambda d:d['n061_owner_status'].update(actual_V5_fits=1))

    def test_invented_provider_product_rejected(self):
        self.rejected(lambda d:d['provider_capabilities'][-1].update(status='COMPLETE'))

    def test_private_recipe_rejected(self):
        self.rejected(lambda d:d['n061_owner_status'].update(feature_columns=['private']))

    def test_new_full_prediction_feed_rejected(self):
        self.rejected(lambda d:d.update(n060_model_rows=[dict(value=.6)]))

    def test_source_probability_leak_rejected(self):
        self.rejected(lambda d:d['games'][0]['source_coverage'][0]['horizons'][-1].update(value=.6))

    def test_new_missing_primary_provider_rejected(self):
        self.rejected(lambda d:d['games'][0]['source_coverage'].pop())


if __name__ == '__main__':
    unittest.main()
