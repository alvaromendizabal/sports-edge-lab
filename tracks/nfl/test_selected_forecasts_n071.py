"""N070 actual owner truth and immutable selected forecast publication."""
import copy,json,unittest
from pathlib import Path
from selected_review_n071 import render
HERE=Path(__file__).resolve().parent

class ActualN070Publication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((HERE/'selected_forecasts_n071.json').read_bytes())
        cls.prior=json.loads((HERE/'selected_forecasts_n070.json').read_bytes())
    def test_page_reopens_as_exact_saved_data(self):
        self.assertEqual((HERE/'season_review_n071.html').read_text(),render(self.data))
    def test_no_fabricated_forecast_or_promotion(self):
        self.assertEqual(self.data['selected_historical_roles'],self.prior['selected_historical_roles'])
        self.assertEqual(self.data['counts'],self.prior['counts'])
        for old,new in zip(self.prior['games'],self.data['games']):
            self.assertEqual(old['targets'],new['targets'])
            self.assertEqual(old['source_observed_at_utc'],new['source_observed_at_utc'])
            self.assertEqual(old['kickoff_utc'],new['kickoff_utc'])
            self.assertGreater(new['latest_schedule_observed_at_utc'],old['latest_schedule_observed_at_utc'])
            self.assertEqual(new['latest_schedule_observation_release'],'N070')
        self.assertFalse(self.data['automatic_promotion'])
        self.assertEqual(self.data['new_forecast_issues'],0)
    def test_unknown_counts_are_not_displayed_as_zero(self):
        run=self.data['latest_owner_execution']
        for key in ('new_native_fits','new_meta_fits','new_forecast_issues'):self.assertIsNone(run[key])
        self.assertEqual(run['verified_new_fit_minimum'],0)
        self.assertEqual(run['verified_new_issue_minimum'],0)
        self.assertTrue(run['failure_pressure_snapshot_available'])
        self.assertFalse(run['historical_and_frontier_stages_invoked'])
        self.assertFalse(run['owner_12_worker_benchmark_completed'])
        self.assertIn("value===null||value===undefined?'unresolved'",render(self.data))
        self.assertNotIn('0 new native fits, 0 new meta fits, 0 new forecasts',render(self.data))
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
        self.assertEqual(src['new_normalized_market_rows'],464)
        self.assertEqual([(x['provider'],x['normalized_rows'])for x in src['provider_coverage']],[('kalshi',164),('polymarket',300)])
        self.assertEqual(src['qualified_current_market_winner_baseline_rows'],0)
        self.assertFalse(src['model_predictions_refreshed']);self.assertFalse(src['all_sources_complete'])
        for provider in ('kalshi','polymarket'):
            rows=[g['current_source_coverage'][provider]for g in self.data['games']]
            self.assertEqual(sum(r['observation_status']=='CAPTURED_WITH_TARGET_GAPS'for r in rows),27)
            self.assertEqual(sum(r['observation_status']=='NOT_REFRESHED_FOR_THIS_GAME_IN_N070'for r in rows),245)
    def test_only_rounded_public_outputs(self):
        text=json.dumps(self.data)
        for token in ('recipe_id','private_source_index','s3://','api_key','FITTED_MODEL.bin'):
            self.assertNotIn(token,text)
        for role in self.data['selected_historical_roles']:
            for card in role['season_metrics']:
                self.assertEqual(card['selection_exposure'],'DEVELOPMENT_EXPOSED')
                self.assertIn(card['season'],(2024,2025))
    def test_embedded_data_escaped(self):
        d=copy.deepcopy(self.data);d['qualifications'].append('</script><script>unsafe()</script>')
        self.assertNotIn('</script><script>unsafe()</script>',render(d))

if __name__=='__main__':unittest.main()
