import copy
import gzip
import json
import unittest
import build_season_comparison as b
import forward_forecasts_public as f

class ForwardForecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=b.ROOT;config=b.read_json(root/'season_comparison_sources.json')[0]
        inputs=[b.read_json(root/config[k])[0] for k in ['selected_outputs','model_review','acceptance','cohort_leaders']]
        cls.base=b.project(*inputs)
        b.apply_current_inventory(cls.base,b.read_json(root/'current_game_inventory.json')[0])
        cls.base['equal_population_evaluation']=b.read_json(root/'equal_cohort_scoreboard.json')[0]
        cls.base['model_market_comparison']=b.read_json(root/'model_market_comparison.json')[0]
        cls.value=b.read_json(root/'forward_forecasts_public.json.gz')[0]

    def fixture(self):
        row=copy.deepcopy(self.value['rows'][0]);base=copy.deepcopy({k:v for k,v in self.base.items() if k!='games'})
        base['games']=[copy.deepcopy(next(g for g in self.base['games'] if g['game_id']==row['game_id']))]
        value=copy.deepcopy({k:v for k,v in self.value.items() if k!='rows'});value['rows']=[row]
        return base,value,row

    def test_all_actual_issues_reconcile_fixed_schedule_and_leave_scores_unchanged(self):
        base=copy.deepcopy(self.base);before=copy.deepcopy((base['champions'],base['equal_population_evaluation'],base['model_market_comparison']))
        s=f.apply_public(base,self.value)
        self.assertEqual((s['new_original_issue_rows'],s['new_distinct_games'],s['new_selected_recipes']),(13601,972,14))
        self.assertEqual(s['actual_issue_classes'],{'EARLY_OUTLOOK':13594,'LATE':7})
        self.assertEqual((s['scheduled_regular_games'],s['scheduled_games_all_roles_new'],s['scheduled_games_partly_updated'],s['scheduled_games_only_older_issues']),(1005,971,1,33))
        self.assertEqual((s['scheduled_selected_role_cells_retaining_older_issues'],s['scheduled_selected_role_cells_missing']),(737,0))
        self.assertEqual((s['new_selected_role_views'],s['superseded_selected_role_issues_preserved']),(21373,21373))
        self.assertEqual(s['nominal_window_issues'],0)
        self.assertEqual(before,(base['champions'],base['equal_population_evaluation'],base['model_market_comparison']))
        by={g['game_id']:g for g in base['games']};original={g['game_id']:g for g in self.base['games']}
        for gid in s['older_only_game_ids']:self.assertEqual(by[gid]['forecasts'],original[gid]['forecasts'])
        for row in self.value['rows']:
            for role in row['roles']:
                self.assertEqual(by[row['game_id']]['forecasts'][role]['prediction'],row['prediction'])
                self.assertEqual(by[row['game_id']]['original_issue_history'][role],[original[row['game_id']]['forecasts'][role]])

    def test_future_source_and_training_clocks_rejected(self):
        for key in ['source_asof_utc','training_cutoff_utc']:
            base,value,row=self.fixture();row[key]='2099-01-01T00:00:00Z'
            with self.assertRaisesRegex(ValueError,'clock invalid'):f.apply_public(base,value)

    def test_wrong_team_and_tip_rejected(self):
        for key,value in [('home_team','WRONG'),('scheduled_start_utc','2099-01-01T00:00:00Z')]:
            base,data,row=self.fixture();row[key]=value
            with self.assertRaisesRegex(ValueError,'identity'):f.apply_public(base,data)

    def test_early_outlook_cannot_be_relabelled_nominal(self):
        base,value,row=self.fixture();row['issue_horizon_class']='NOMINAL'
        with self.assertRaisesRegex(ValueError,'Nominal'):f.apply_public(base,value)

    def test_actual_lead_must_match_original_clock(self):
        base,value,row=self.fixture();row['actual_lead_minutes']+=60
        with self.assertRaisesRegex(ValueError,'lead changed'):f.apply_public(base,value)

    def test_duplicate_issue_rejected(self):
        base,value,row=self.fixture();value['rows'].append(copy.deepcopy(row))
        with self.assertRaisesRegex(ValueError,'Duplicate original'):f.apply_public(base,value)

    def test_candidate_without_selected_role_rejected(self):
        base,value,row=self.fixture();row['roles']=[]
        with self.assertRaisesRegex(ValueError,'Candidate grid'):f.apply_public(base,value)

    def test_role_reselection_rejected(self):
        base,value,row=self.fixture();value['role_bindings'][row['roles'][0]]='candidate-0123456789ab'
        with self.assertRaisesRegex(ValueError,'role binding'):f.apply_public(base,value)

    def test_private_model_material_rejected(self):
        base,value,row=self.fixture();row['recipe_id']='private'
        with self.assertRaisesRegex(ValueError,'Private'):f.apply_public(base,value)

    def test_older_projection_cannot_replace_newer_original_issue(self):
        base,value,row=self.fixture();base['games'][0]['forecasts'][row['roles'][0]]['issued_at_utc']='2099-01-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError,'overwrite newer'):f.apply_public(base,value)

    def test_poststart_issue_cannot_enter_forward_pregame_projection(self):
        base,value,row=self.fixture();row['issued_at_utc']=row['scheduled_start_utc']
        with self.assertRaisesRegex(ValueError,'clock invalid'):f.apply_public(base,value)

    def test_forward_update_cannot_claim_test_backscore_or_promotion(self):
        for key,value in [('automatic_promotions',1),('historical_test_backscore',True)]:
            base,data,row=self.fixture();data[key]=value
            with self.assertRaisesRegex(ValueError,'alter science'):f.apply_public(base,data)

if __name__=='__main__':unittest.main()
