"""N071 actual output and latest selected publication contracts."""
import copy,json,unittest
from pathlib import Path
from selected_review_n072 import render
HERE=Path(__file__).resolve().parent

class ActualN071Publication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((HERE/'selected_forecasts_n072.json').read_bytes())
        cls.prior=json.loads((HERE/'selected_forecasts_n071.json').read_bytes())
    def test_page_reopens_as_exact_saved_data(self):
        self.assertEqual((HERE/'season_review_n072.html').read_text(),render(self.data))
    def test_no_new_historical_champion_or_promotion(self):
        self.assertEqual(self.data['selected_historical_roles'],self.prior['selected_historical_roles'])
        self.assertFalse(self.data['automatic_promotion'])
        self.assertEqual(self.data['new_forecast_issues'],0)
        self.assertFalse(self.data['latest_owner_execution']['new_champion_promotion'])
    def test_honest_phase_count_scope(self):
        r=self.data['latest_owner_execution']
        self.assertEqual(r['new_native_fits'],4)
        self.assertEqual(r['new_meta_fits'],0)
        self.assertEqual(r['raw_phase_sum_forecast_rows'],1344)
        self.assertEqual(r['latest_selected_rows'],448)
        self.assertEqual(r['latest_selected_games'],112)
        self.assertEqual(r['distinct_new_forecast_issues'],1344)
        self.assertEqual(r['distinct_game_model_target_combinations'],448)
        self.assertEqual(r['issue_batches'],3)
        self.assertIn('not independent',r['forecast_count_qualification'])
        self.assertEqual(r['observed_native_fit_concurrency'],1)
        self.assertEqual(r['observed_leased_process_concurrency'],3)
        self.assertFalse(r['owner_research_acceptance'])
    def test_latest_issues_keep_real_pregame_clocks(self):
        from datetime import datetime
        rows=[]
        for g in self.data['games']:
            for t in g['targets'].values():
                for r in t['current_forecasts']:
                    self.assertLess(datetime.fromisoformat(r['original_issue_at_utc']),datetime.fromisoformat(g['kickoff_utc']))
                    self.assertLessEqual(datetime.fromisoformat(r['model_completed_at_utc']),datetime.fromisoformat(r['original_issue_at_utc']))
                    self.assertTrue(r['original_issue_at_utc'].startswith('2026-11-11T18:15:'))
                    self.assertEqual(r['evidence_kind'],'original_issued');rows.append(r)
        self.assertEqual(len(rows),448)
    def test_retained_panels_not_rewritten(self):
        for old,new in zip(self.prior['games'],self.data['games']):
            self.assertEqual(old['game_id'],new['game_id'])
            self.assertEqual(old['kickoff_utc'],new['kickoff_utc'])
            self.assertEqual(old['home_score'],new['home_score'])
            self.assertEqual(old['away_score'],new['away_score'])
            for target in ('win','margin','total'):
                for row in old['targets'][target]['earlier_saved_forward']:
                    self.assertIn(row,new['targets'][target]['earlier_saved_forward'])
                self.assertEqual(old['targets'][target]['prior_selected_reconstruction'],new['targets'][target]['prior_selected_reconstruction'])
    def test_complete_denominators(self):
        games=self.data['games'];c=self.data['counts']
        self.assertEqual(len(games),272);self.assertEqual(len({g['game_id']for g in games}),272)
        self.assertEqual(sum(g['completed_in_saved_census']for g in games),136)
        self.assertEqual(sum(g['official_time_tbd']for g in games),24)
        self.assertEqual(c['current_selected_games'],112);self.assertEqual(c['current_selected_rows'],448)
        self.assertTrue(all(set(g['targets'])=={'win','margin','total'}for g in games))
        self.assertTrue(all(g['kickoff_utc']is None for g in games if g['official_time_tbd']))
    def test_new_source_counts_and_missingness(self):
        src=self.data['latest_source_refresh']
        self.assertEqual(src['new_normalized_market_rows'],468)
        self.assertEqual([(x['provider'],x['normalized_rows'])for x in src['provider_coverage']],[('kalshi',164),('polymarket',304)])
        self.assertEqual(src['qualified_current_market_winner_baseline_rows'],0)
        self.assertTrue(src['model_predictions_refreshed']);self.assertFalse(src['all_sources_complete'])
        for provider in ('kalshi','polymarket'):
            rows=[g['current_source_coverage'][provider]for g in self.data['games']]
            self.assertEqual(sum(r['observation_status']=='CAPTURED_WITH_TARGET_GAPS'for r in rows),27)
            self.assertEqual(sum(r['observation_status']=='NOT_REFRESHED_FOR_THIS_GAME_IN_N071'for r in rows),245)
    def test_public_fields_and_no_rounded_rescoring(self):
        text=json.dumps(self.data)
        for token in ('recipe_id','private_source_index','s3://','api_key','FITTED_MODEL.bin'):
            self.assertNotIn(token,text)
        self.assertFalse(self.data['rounding']['metrics_from_rounded_values'])
        for role in self.data['selected_historical_roles']:
            for card in role['season_metrics']:
                self.assertEqual(card['selection_exposure'],'DEVELOPMENT_EXPOSED')
                self.assertIn(card['season'],(2024,2025))
    def test_embedded_data_escaped(self):
        d=copy.deepcopy(self.data);d['qualifications'].append('</script><script>unsafe()</script>')
        self.assertNotIn('</script><script>unsafe()</script>',render(d))

if __name__=='__main__':unittest.main()
