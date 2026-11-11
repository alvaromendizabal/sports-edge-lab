"""Public selected outputs, denominator and page consistency; no real fitting."""
import copy
import json
from pathlib import Path
import unittest
from selected_review_page import render

HERE=Path(__file__).resolve().parent

class SelectedForecastPublication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=json.loads((HERE/'selected_forecasts_n069.json').read_bytes())
    def test_page_exactly_matches_saved_projection(self):
        self.assertEqual((HERE/'season_review_n069.html').read_text(),render(self.data))
    def test_complete_schedule_and_target_denominators(self):
        d=self.data;games=d['games'];counts=d['counts']
        self.assertEqual(len(games),counts['schedule_games'])
        self.assertEqual(len({g['game_id']for g in games}),len(games))
        self.assertEqual(sum(g['completed_in_saved_census']for g in games),counts['completed_games'])
        self.assertEqual(sum(g['official_time_tbd']for g in games),counts['official_time_tbd_games'])
        self.assertTrue(all(set(g['targets'])=={'win','margin','total'}for g in games))
    def test_all_evidence_union_is_explicit_and_not_forward_score(self):
        groups=('current_forecasts','earlier_saved_forward','prior_selected_reconstruction')
        count=sum(any(panel[group]for panel in g['targets'].values()for group in groups)for g in self.data['games'])
        self.assertEqual(count,self.data['counts']['games_with_any_preserved_evidence'])
        self.assertEqual(len(self.data['games'])-count,self.data['counts']['games_without_prediction_evidence_in_this_projection'])
        self.assertFalse(self.data['automatic_promotion'])
        self.assertEqual(self.data['new_model_fits'],0)
        self.assertEqual(self.data['new_model_inference'],0)
        self.assertEqual(self.data['new_forecast_issues'],0)
    def test_tbd_placeholder_is_not_a_clock(self):
        for game in self.data['games']:
            if game['official_time_tbd']:
                self.assertIsNone(game['kickoff_utc'])
                self.assertTrue(all(not panel['current_forecasts']for panel in game['targets'].values()))
    def test_current_issue_role_availability_is_exact(self):
        for game in self.data['games']:
            for panel in game['targets'].values():
                aliases={r['model_alias']for r in panel['current_forecasts']}
                for role in panel['roles']:
                    self.assertEqual(role['current_forecast_available'],role['model_alias']in aliases)
                    if not role['current_forecast_available']:self.assertTrue(role['missing_reason'])
    def test_reconstructed_rows_do_not_acquire_original_issue(self):
        for game in self.data['games']:
            for panel in game['targets'].values():
                for row in panel['prior_selected_reconstruction']:
                    self.assertIsNone(row['original_issue_at_utc'])
                    self.assertEqual(row['evidence_kind'],'historical_reconstruction')
                    self.assertIn('never originally issued',row['evidence_class'])
    def test_no_private_material_or_full_precision_candidate_grid(self):
        text=json.dumps(self.data)
        for token in ('recipe_id','private_source_index','s3://','/home/sagemaker-user','/workspace/','model_pointer','raw_provider_url'):
            self.assertNotIn(token,text)
        self.assertFalse(self.data['evidence_checks']['full_candidate_grid_published'])
        self.assertFalse(self.data['rounding']['metrics_from_rounded_values'])
    def test_season_scorecards_preserve_exposed_role(self):
        roles=self.data['selected_historical_roles']
        self.assertEqual(len({r['role_id']for r in roles}),len(roles))
        for role in roles:
            self.assertEqual(role['selection_seasons'],[2024,2025])
            for card in role['season_metrics']:
                self.assertEqual(card['selection_exposure'],'DEVELOPMENT_EXPOSED')
                self.assertIn(card['season'],(2024,2025))
    def test_html_data_cannot_escape_script_container(self):
        value=copy.deepcopy(self.data);value['qualifications'].append('</script><script>unsafe()</script>')
        self.assertNotIn('</script><script>unsafe()</script>',render(value))

if __name__=='__main__':unittest.main()
