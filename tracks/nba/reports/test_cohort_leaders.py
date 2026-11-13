"""Preserve saved exact-cohort boundaries; no model fitting or rescoring."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_cohort_leaders as subject

ROOT=Path(__file__).parent
class SavedCohortLeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'current_saved_cohort_leaders.json').read_bytes())
        cls.model=json.loads((ROOT/'latest_model_review.json').read_bytes())

    def test_twenty_saved_leaders_have_eight_distinct_verified_supports(self):
        self.assertEqual(subject.validate(self.data,self.model),{'rows':20,'distinct_exact_cohorts':8})
        self.assertEqual(sum(len(row['source_rows']) for row in self.data['rows']),27)
        self.assertTrue(all(row['scored_games']+row['missing_games']==row['completed_game_denominator'] for row in self.data['rows']))
        self.assertTrue(any(row['distinct_saved_recipes']==1 for row in self.data['rows']))

    def test_changed_saved_metric_or_row_alias_is_rejected(self):
        for action,error in [(lambda x:x['rows'][0].update(saved_metric_value=0),'SAVED_SCORE_CHANGED'),(lambda x:x['rows'][0]['source_rows'][0].update(role_alias='different'),'SOURCE_ROW_IDENTITY')]:
            value=copy.deepcopy(self.data);action(value)
            with self.assertRaisesRegex(ValueError,error):subject.validate(value,self.model)

    def test_current_exposure_cannot_become_full_season_or_prospective_claim(self):
        for key in ['entire_current_season_best_claim','original_issue_claim','independent_confirmation_claim']:
            value=copy.deepcopy(self.data);value[key]=True
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'EXPOSURE_OR_SCOPE'):subject.validate(value,self.model)
        value=copy.deepcopy(self.data);value['rows'][0]['selection_or_promotion_allowed']=True
        with self.assertRaisesRegex(ValueError,'ROW_SCOPE'):subject.validate(value,self.model)

    def test_missing_games_and_distinct_cohorts_cannot_be_collapsed(self):
        value=copy.deepcopy(self.data);value['rows'][0]['missing_games']=0
        with self.assertRaisesRegex(ValueError,'DENOMINATOR'):subject.validate(value,self.model)
        value=copy.deepcopy(self.data);value['rows'][2]['cohort_alias']=value['rows'][0]['cohort_alias']
        with self.assertRaisesRegex(ValueError,'DUPLICATE_METRIC|DISTINCT_SUPPORTS_COLLAPSED'):subject.validate(value,self.model)

    def test_new_public_model_snapshot_cannot_reuse_old_cohort_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'current_saved_cohort_leaders.json').write_bytes((ROOT/'current_saved_cohort_leaders.json').read_bytes())
            value=copy.deepcopy(self.model);value['evidence_as_of_utc']='2099-01-01T00:00:00Z';(root/'latest_model_review.json').write_text(json.dumps(value))
            with patch.object(subject,'ROOT',root),self.assertRaisesRegex(ValueError,'MODEL_REVIEW_PIN_CHANGED'):subject.build(check=True)

    def test_deterministic_display_and_physical_source_pin(self):
        body=(ROOT/'latest_model_review.json').read_bytes()
        self.assertEqual(self.data['source_public_file_pin'],{'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
        self.assertEqual(subject.build(check=True)['status'],'PASS')
        page=(ROOT/'latest_research_outputs.html').read_text();self.assertEqual(subject.attach(page,self.data,self.model),page)

if __name__=='__main__':unittest.main()
