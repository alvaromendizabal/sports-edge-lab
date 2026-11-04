"""Adversarial tests for display-only recovered observations and genuine issues."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from primary_issue import validate_primary_issue, choose_primary_issue
from source_recovery import validate_source_recovery, merged_references

HERE = Path(__file__).resolve().parent


class SourceRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coverage, cls.original, cls.schedule, cls.recovery, cls.primary = [json.loads((HERE/name).read_text()) for name in
            ('current_coverage.json', 'current_source_overlay.json', 'reschedule_reference.json',
             'source_recovery_n036.json', 'primary_issue_n035.json')]

    def check(self, data):
        return validate_source_recovery(data, self.coverage, self.original, self.schedule)

    def test_combined_coverage_and_prior_payload_preservation(self):
        before = deepcopy((self.original, self.schedule, self.coverage))
        receipt = self.check(self.recovery)
        self.assertEqual(before, (self.original, self.schedule, self.coverage))
        for row in receipt['source_recovery_combined_week9_coverage']:
            self.assertEqual(row['available_games'], 13 if row['provider']=='Polymarket' else 15)
        self.assertEqual(receipt['source_recovery_rows'], 13)

    def test_no_historical_cutoff_promotion(self):
        for h in ('T1', 'T2', 'LATEST_PREGAME'):
            x=deepcopy(self.recovery); x['winner_rows'][0]['horizon']=h
            with self.subTest(horizon=h), self.assertRaises(ValueError): self.check(x)

    def test_unknown_nested_private_field_rejected(self):
        x=deepcopy(self.recovery); x['winner_rows'][0]['raw_source']='private'
        with self.assertRaises(ValueError): self.check(x)

    def test_missing_provider_quote_does_not_become_known(self):
        x=deepcopy(self.recovery); x['winner_rows'][0]['quote_at']=x['winner_rows'][0]['acquired_at']
        with self.assertRaises(ValueError): self.check(x)

    def test_stale_malformed_row_is_not_hidden_by_merge(self):
        x=deepcopy(self.recovery); x['point_rows'][0]['point_estimate']=40
        x['point_rows'][0]['acquired_at']='2026-11-01T00:00:00Z'
        with self.assertRaises(ValueError): self.check(x)

    def test_duplicate_cell_rejected(self):
        x=deepcopy(self.recovery); x['point_rows'][1]=deepcopy(x['point_rows'][0])
        with self.assertRaises(ValueError): self.check(x)

    def test_incorrect_coverage_not_accepted(self):
        x=deepcopy(self.recovery); x['combined_week9_coverage'][-1]['available_games']=15
        with self.assertRaises(ValueError): self.check(x)

    def test_source_recovery_never_claims_fits_or_acceptance(self):
        for k,v in [('new_model_fits',1),('new_forecast_issues',1),('owner_pipeline_accepted',True),('historical_metrics_changed',True)]:
            x=deepcopy(self.recovery); x[k]=v
            with self.subTest(field=k), self.assertRaises(ValueError): self.check(x)

    def test_issue_is_29_early_games_without_new_fit_credit(self):
        receipt=validate_primary_issue(self.primary,self.coverage)
        self.assertEqual(receipt['primary_issue_games'],29)
        self.assertEqual(receipt['primary_issue_new_fits'],0)

    def test_issue_cannot_override_a_completed_game_or_other_stream(self):
        card=self.primary['cards'][0]
        game=next(g for g in self.coverage['all_games'] if g['game_id']==card['game_id'])
        other={'model_id':'original_frozen','actual_issue_at':None}
        self.assertIs(choose_primary_issue(game,other,card),other)
        prior={'model_id':card['model_id'],'actual_issue_at':'2026-11-03T00:00:00Z'}
        self.assertIs(choose_primary_issue({**game,'completed':True},prior,card),prior)
        self.assertIs(choose_primary_issue(game,prior,card),card)
        newer={**prior,'actual_issue_at':'2026-11-04T02:00:00Z'}
        self.assertIs(choose_primary_issue(game,newer,card),newer)

    def test_issue_cannot_be_backdated_final_hour_or_injury_promoted(self):
        for k,v in [('horizon','T1'),('injury_inputs_verified',True),('full_pipeline_selection_qualified',True),('correct',True),('model_id','original_frozen')]:
            x=deepcopy(self.primary);x['cards'][0][k]=v
            with self.subTest(field=k),self.assertRaises(ValueError):validate_primary_issue(x,self.coverage)

    def test_issue_source_after_issue_is_rejected(self):
        x=deepcopy(self.primary);x['cards'][0]['source_asof']='2026-11-04T02:00:00Z'
        with self.assertRaises(ValueError):validate_primary_issue(x,self.coverage)

    def test_issue_probability_team_conflict_rejected(self):
        x=deepcopy(self.primary);x['cards'][0]['home_win_probability']=1-x['cards'][0]['home_win_probability']
        with self.assertRaises(ValueError):validate_primary_issue(x,self.coverage)

    def test_issue_hidden_source_payload_rejected(self):
        x=deepcopy(self.primary);x['cards'][0]['raw_source']={'body':'private'}
        with self.assertRaises(ValueError):validate_primary_issue(x,self.coverage)

if __name__=='__main__':unittest.main()
