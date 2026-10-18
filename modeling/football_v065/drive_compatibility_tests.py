import copy,unittest
import pandas as pd
from drive_compatibility import compare_cfbd_primary,fixture_inputs

class DriveCompatibilityTests(unittest.TestCase):
    def setUp(self):self.rows,self.primary,self.games=fixture_inputs()
    def call(self,**kw):
        options=dict(observed_at='2026-10-18T01:00:00Z',as_of='2026-10-18T01:01:00Z',source_sha256='a'*64);options.update(kw)
        return compare_cfbd_primary(self.rows,self.primary,self.games,**options)
    def test_exact_full_reference_is_review_only(self):
        r=self.call();self.assertTrue(r['proof']['semantic_equivalence_proven']);self.assertTrue(r['proof']['candidate_for_manual_review']);self.assertFalse(r['proof']['automatic_serving_authorized']);self.assertEqual(r['audit']['model_feature_insertions'],0)
    def test_fbs_context_separate(self):
        r=self.call();self.assertEqual(r['audit']['normalized_strict_FBS_games'],1);self.assertEqual(r['audit']['normalized_declared_opponent_context_games'],1)
    def test_no_observation_does_not_renew(self):self.assertFalse(self.call(observed_at=None)['proof']['fresh_observation_verified'])
    def test_old_original_observation_not_renewal(self):self.assertFalse(self.call(observed_at='2026-10-16T18:15:25Z')['proof']['fresh_observation_verified'])
    def test_stale_observation(self):self.assertFalse(self.call(observed_at='2026-10-16T20:00:00Z')['proof']['fresh_observation_verified'])
    def test_future_observation(self):self.assertFalse(self.call(observed_at='2026-10-19T01:00:00Z')['proof']['fresh_observation_verified'])
    def test_naive_observation(self):self.assertFalse(self.call(observed_at='2026-10-18T01:00:00')['proof']['fresh_observation_verified'])
    def test_missing_source_hash_no_renewal(self):self.assertFalse(self.call(source_sha256=None)['proof']['candidate_for_manual_review'])
    def test_wrong_hash_shape_no_renewal(self):self.assertFalse(self.call(source_sha256='g'*64)['proof']['candidate_for_manual_review'])
    def test_unchanged_unknown_publication(self):self.assertIsNone(self.call()['proof']['source_publication_at'])
    def test_missing_game_fails_complete(self):
        self.rows=self.rows[:8];r=self.call();self.assertEqual(r['proof']['missing_prior_game_ids'],['1002']);self.assertFalse(r['proof']['semantic_equivalence_proven'])
    def test_metric_change_fails(self):
        self.rows[0]['yards']=31;r=self.call();self.assertEqual(r['proof']['mismatching_prior_game_ids'],['1001']);self.assertFalse(r['proof']['semantic_equivalence_proven'])
    def test_denominator_change_fails(self):
        self.rows[0]['plays']=6;self.assertFalse(self.call()['proof']['semantic_equivalence_proven'])
    def test_result_change_fails(self):
        self.rows[0]['driveResult']='PUNT';self.assertFalse(self.call()['proof']['semantic_equivalence_proven'])
    def test_ambiguous_team_names_quarantine_entire_game(self):
        self.rows[0]['offense']='Elsewhere';r=self.call();self.assertIn('1001',r['audit']['quarantined_game_ids']);self.assertNotIn('1001',set(r['normalized_stats'].game_id))
    def test_home_boolean_exact(self):
        self.rows[0]['isHomeOffense']='True';self.assertFalse(self.call()['proof']['semantic_equivalence_proven'])
    def test_bool_plays_invalid(self):
        self.rows[0]['plays']=True;self.assertIn('1001',self.call()['audit']['quarantined_game_ids'])
    def test_fractional_plays_invalid(self):
        self.rows[0]['plays']=5.1;self.assertIn('1001',self.call()['audit']['quarantined_game_ids'])
    def test_nonfinite_yards_invalid(self):
        self.rows[0]['yards']=float('nan');self.assertIn('1001',self.call()['audit']['quarantined_game_ids'])
    def test_unknown_eligible_result_does_not_drop_and_accept(self):
        self.rows[0]['driveResult']='Uncategorized';r=self.call();self.assertIn('1001',r['audit']['quarantined_game_ids']);self.assertNotIn('1001',set(r['normalized_stats'].game_id))
    def test_conflicting_duplicate_blocks_game(self):
        x=copy.deepcopy(self.rows[0]);x['yards']=29;self.rows.append(x);self.assertFalse(self.call()['proof']['semantic_equivalence_proven'])
    def test_identical_duplicate_no_metric_change(self):
        self.rows.append(copy.deepcopy(self.rows[0]));self.assertTrue(self.call()['proof']['semantic_equivalence_proven'])
    def test_no_inventory_weakening(self):
        with self.assertRaises(ValueError):self.call(required_primary_game_ids=['1001'])
    def test_missing_declared_context_canonical_cannot_weaken_inventory(self):
        self.games=self.games[self.games.game_id!='1002']
        with self.assertRaisesRegex(ValueError,'Primary metric inventory missing'):self.call()
    def test_missing_strict_fbs_canonical_cannot_weaken_inventory(self):
        self.games=self.games[self.games.game_id!='1001']
        with self.assertRaisesRegex(ValueError,'Primary metric inventory missing'):self.call()
    def test_misclassified_canonical_season_cannot_drop_primary(self):
        self.games.loc[self.games.game_id=='1002','season']=2025
        with self.assertRaisesRegex(ValueError,'Primary metric inventory missing'):self.call()
    def test_primary_other_track_refused_without_filter(self):
        self.primary.loc[self.primary.index[0],'track']='nfl'
        with self.assertRaisesRegex(ValueError,'only NCAAF'):self.call()
    def test_primary_wrong_season_refused(self):
        self.primary['season']=2026;self.primary.loc[self.primary.index[0],'season']=2025
        with self.assertRaisesRegex(ValueError,'season mismatch'):self.call()
    def test_primary_explicit_current_season_preserves_full_inventory(self):
        self.primary['season']=2026
        self.assertEqual(self.call()['proof']['required_primary_games'],2)
    def test_reference_pair_required(self):
        self.primary=self.primary.iloc[1:];
        with self.assertRaises(ValueError):self.call()
    def test_duplicate_reference_refused(self):
        self.primary=pd.concat([self.primary,self.primary.iloc[:1]])
        with self.assertRaises(ValueError):self.call()
    def test_empty_payload_reports_all_missing(self):
        self.rows=[];r=self.call();self.assertEqual(len(r['proof']['missing_prior_game_ids']),2);self.assertEqual(len(r['normalized_stats']),0)
    def test_non_list_response_refused(self):
        self.rows={};
        with self.assertRaises(ValueError):self.call()
    def test_future_game_ignored_without_backdating(self):
        x=copy.deepcopy(self.rows[0]);x.update(gameId=1003,id='10031');self.rows.append(x);r=self.call();self.assertEqual(r['audit']['excluded_reason_counts']['canonical_game_not_completed'],1)
    def test_no_auto_semantic_stamp_in_output(self):self.assertNotIn('semantic_contract',self.call()['normalized_stats'].columns)
    def test_no_fit_or_forecast(self):
        r=self.call();self.assertEqual(r['audit']['new_model_fits'],0);self.assertEqual(r['audit']['new_forecasts'],0)
    def test_overtime_excluded(self):
        x=copy.deepcopy(self.rows[0]);x.update(id='100199',startPeriod=5,endPeriod=5);self.rows.append(x);self.assertTrue(self.call()['proof']['semantic_equivalence_proven'])
    def test_backward_period_quarantines_game_without_changing_primary(self):
        original=self.primary.copy(deep=True)
        self.rows[0].update(startPeriod=4,endPeriod=1)
        r=self.call()
        self.assertIn('1001',r['audit']['quarantined_game_ids'])
        self.assertNotIn('1001',set(r['normalized_stats'].game_id))
        self.assertFalse(r['proof']['semantic_equivalence_proven'])
        self.assertFalse(r['proof']['candidate_for_manual_review'])
        self.assertTrue(any(x['reason']=='Drive end period precedes start period' for x in r['quarantine']))
        pd.testing.assert_frame_equal(self.primary,original)
    def test_period_end_excluded(self):
        x=copy.deepcopy(self.rows[0]);x.update(id='100199',driveResult='END OF HALF');self.rows.append(x);self.assertTrue(self.call()['proof']['semantic_equivalence_proven'])

if __name__=='__main__':unittest.main()
