import copy,json,pathlib,re,unittest
from build_review_n050 import build,validate
from export_site_n050 import projection
ROOT=pathlib.Path(__file__).resolve().parent


class CurrentReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=json.loads((ROOT/'current_review_n050.json').read_text())

    def test_generated_review_matches_sanitized_source(self):
        self.assertEqual((ROOT/'review_n050.html').read_text(),build(self.data))

    def test_all_games_and_actual_issued_counts_are_distinct(self):
        d=self.data
        self.assertEqual(len(d['games']),272)
        self.assertEqual(sum(g['completed'] for g in d['games']),122)
        self.assertEqual(len(d['cards']),56)
        self.assertEqual(d['new_target_forecasts'],168)
        self.assertEqual(d['new_native_fits'],0)
        self.assertEqual(len({c['game_id'] for c in d['cards']}),28)

    def test_started_game_has_result_and_no_new_card(self):
        game=next(g for g in self.data['games'] if g['game_id']=='2026_09_JAX_BAL')
        self.assertEqual(game['actual']['home_margin'],-23)
        self.assertFalse(any(c['game_id']==game['game_id'] for c in self.data['cards']))

    def test_missing_provider_cells_survive(self):
        d=self.data
        self.assertEqual(len(d['winner_references']),87)
        self.assertEqual(len(d['point_references']),174)
        for week,provider,expected in [(9,'DraftKings',14),(10,'DraftKings',13),(10,'Kalshi',0),(10,'Polymarket',0)]:
            for target in ['winner','margin','total']:
                row=next(r for r in d['provider_coverage'] if r['week']==week and r['provider']==provider and r['target']==target)
                self.assertEqual(row['available_games'],expected)

    def test_unknown_quote_time_stays_unknown(self):
        observed=[r for r in self.data['winner_references'] if r['provider']=='Kalshi' and r['availability_status'].startswith('OBSERVED')]
        self.assertEqual(len(observed),14)
        self.assertTrue(all(r['quote_at'] is None and r['acquired_at'] for r in observed))

    def test_target_fit_clocks_and_old_base_snapshot_preserved(self):
        for c in self.data['cards']:
            self.assertEqual(set(c['fit_completed_by_target']),{'win','margin','total'})
            self.assertTrue(c['base_feature_asof'].startswith('2026-11-04'))
        shadow=next(c for c in self.data['cards'] if c['stream_id']=='n049_shadow')
        self.assertIsNone(shadow['injury_max_report_at'])

    def test_no_private_source_or_active_recipe_fields(self):
        serialized=json.dumps(self.data)
        self.assertIsNone(re.search(r's3://|arn:aws:|/workspace/|/home/|X-Amz-|AKIA[A-Z0-9]{16}|component_bindings|candidate|registration_sha256|model_sha256',serialized))

    def test_preparation_cannot_award_execution(self):
        for field in ['owner_native_fits','owner_forecasts']:
            d=copy.deepcopy(self.data);d['next'][field]=1
            with self.assertRaises(ValueError):validate(d)

    def test_source_windows_cannot_award_fits(self):
        d=copy.deepcopy(self.data);d['completed_source']['new_market_path_fits']=1
        with self.assertRaises(ValueError):validate(d)

    def test_actual_acceptance_cannot_be_upgraded(self):
        d=copy.deepcopy(self.data);d['owner_research_accepted']=True
        with self.assertRaises(ValueError):validate(d)

    def test_hosted_projection_preserves_every_old_embedded_dataset(self):
        original=(ROOT/'review.html').read_text();current=build(self.data)
        published,archive=projection(current,original,json.loads((ROOT/'readiness_n049.json').read_text()),'a'*40)
        pattern=r'<script[^>]*type="application/json"[^>]*>(.*?)</script>'
        self.assertEqual(re.findall(pattern,original,re.S),re.findall(pattern,archive,re.S))
        self.assertIn('Historical view through N048',archive)
        self.assertIn('href="history.html#latest-coverage"',published)
        self.assertIn('Canonical commit:',published)
        self.assertEqual(re.findall(pattern,current,re.S),re.findall(pattern,published,re.S))

    def test_unpinned_projection_rejected(self):
        with self.assertRaises(ValueError):projection(build(self.data),'',{},'main')

if __name__=='__main__':unittest.main()
