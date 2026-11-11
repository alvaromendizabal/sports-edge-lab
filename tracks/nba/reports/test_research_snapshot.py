"""Public source-separated snapshot checks; no fitting or metric rescoring."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest


ROOT=Path(os.environ.get('NBA_SNAPSHOT_TEST_DIR',Path(__file__).parent))
SPEC=importlib.util.spec_from_file_location('nba_public_snapshot_validator',ROOT/'validate_research_snapshot.py')
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR)


class SourceSeparatedSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved=json.loads((ROOT/'latest_research_outputs.json').read_bytes())

    def test_complete_observed_schedule_and_saved_output_contract(self):
        checks=VALIDATOR.validate_public_report(self.saved)
        self.assertEqual(checks['official_schedule_games'],self.saved['coverage']['official_schedule_games'])
        self.assertEqual(checks['all_game_target_horizon_cells'],6*len(self.saved['games']))

    def test_schedule_and_result_clocks_remain_distinct(self):
        rows=[game for game in self.saved['games'].values() if game.get('result_observation')]
        self.assertEqual(len(rows),self.saved['result_observation_recovery'].get('result_rows_attached',0))
        for game in rows:
            result=game['result_observation']
            self.assertEqual(game['last_confirmed_status'],'FINAL')
            self.assertEqual(game['last_confirmed_status_asof_utc'],result['observed_at_utc'])
            self.assertEqual(game['official_status_at_source'],game['source_status'])
            self.assertFalse(result['original_historical_possession_claim'])
            self.assertFalse(result['new_score_calculation'])

    def test_count_only_live_status_cannot_be_assigned_to_an_unidentified_game(self):
        changed=copy.deepcopy(self.saved)
        game=next(row for row in changed['games'].values()
                  if row['source_status']=='SCHEDULED' and not row.get('result_observation'))
        game['last_confirmed_status']='LIVE'
        with self.assertRaisesRegex(ValueError,'not supported'):
            VALIDATOR.validate_public_report(changed)

    def test_aggregate_row_disagreement_cannot_be_hidden(self):
        if not self.saved['coverage']['latest_row_and_source_aggregate_difference']:
            self.skipTest('This saved snapshot contains no aggregate-only status difference')
        changed=copy.deepcopy(self.saved);changed['coverage']['latest_row_and_source_aggregate_difference']={}
        with self.assertRaisesRegex(ValueError,'discrepancy hidden'):
            VALIDATOR.validate_public_report(changed)

    def test_results_cannot_be_redated_to_future_publication(self):
        changed=copy.deepcopy(self.saved)
        result=next(row['result_observation'] for row in changed['games'].values() if row.get('result_observation'))
        result['observed_at_utc']='2099-01-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError,'information clock'):
            VALIDATOR.validate_public_report(changed)

    def test_private_model_fields_are_rejected(self):
        changed=copy.deepcopy(self.saved);changed['recipe_id']='PRIVATE_NOT_AUTHORIZED'
        with self.assertRaisesRegex(ValueError,'Private field'):
            VALIDATOR.validate_public_report(changed)


if __name__=='__main__':unittest.main()
