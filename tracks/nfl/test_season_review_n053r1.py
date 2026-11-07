"""Scientific boundaries of the full-season presentation."""
import copy,json,pathlib,re,unittest
from build_season_review_n053r1 import validate,build,load,pack,RETIRED
HERE=pathlib.Path(__file__).resolve().parent

class FullSeasonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load()
        cls.games={g['game_id']:g for g in cls.data['games']}
    def test_restored_source_comparisons_remain_separate(self):
        d=self.data;self.assertEqual(d['restored_source_reconciliation']['Polymarket_old_missing_games_restored'],29);self.assertEqual(d['restored_source_reconciliation']['Polymarket_completed_source_games'],122)
        rows=[r for r in d['restored_source_comparison_metrics'] if r['scope']=='EXACT_RESTORED_COMMON_THREE_PROVIDER_T2'];self.assertEqual(len(rows),3);self.assertEqual({r['games'] for r in rows},{119});self.assertEqual({r['identity'] for r in rows},{'DraftKings','Kalshi','Polymarket'})
        old=[r for r in d['restored_source_comparison_metrics'] if r['scope']=='PRESERVED_DESCRIPTIVE_MODEL_91_COMMON_T2'];self.assertEqual({r['games'] for r in old},{91});self.assertTrue(all(not r['original_metric_changed'] and not r['statistical_significance_claimed'] and not r['automatic_promotion'] for r in d['restored_source_comparison_metrics']))
        self.assertEqual(len(d['restored_source_paired_comparisons']),9)
    def test_complete_schedule_and_equal_grid(self):
        d=validate(self.data)
        self.assertEqual(len(d['model_rows']),272*len(d['lanes'])*3)
        self.assertEqual(len(d['provider_rows']),272*3*3*len(d['provider_horizons']))
        self.assertEqual(len({g['away'] for g in d['games']}|{g['home'] for g in d['games']}),32)
    def test_recent_finals_preserve_separate_actual_issues(self):
        for game,lane in [('2026_08_CHI_SEA','preserved_selected_actual_T1'),('2026_09_JAX_BAL','latest_resolved_fresh')]:
            g=self.games[game];self.assertTrue(g['completed']);self.assertFalse(g['frozen_point_benchmark'])
            rows=[r for r in self.data['model_rows'] if r['game_id']==game and r['lane_id']==lane]
            self.assertEqual(len(rows),3);self.assertTrue(all(r['available'] and r['actual_issue_eligible'] for r in rows))
        self.assertEqual(self.games['2026_08_CHI_SEA']['actual']['away_score'],34)
        self.assertEqual(self.games['2026_08_CHI_SEA']['actual']['home_score'],17)
        self.assertEqual(self.games['2026_09_JAX_BAL']['actual']['home_margin'],-23)
    def test_benchmark_does_not_replace_completed_denominator(self):
        self.assertEqual(sum(g['frozen_point_benchmark'] for g in self.data['games']),120)
        self.assertEqual(sum(g['frozen_binary_benchmark'] for g in self.data['games']),119)
        self.assertEqual({r['denominator'] for r in self.data['coverage_rows']},{122})
        self.assertTrue(any(r['count']==92 for r in self.data['denominator_bridge']))
        self.assertTrue(any(r['count']==91 for r in self.data['denominator_bridge']))
    def test_horizons_and_direction_only_records_stay_distinct(self):
        rows=self.data['provider_rows'];self.assertTrue({'T1','T2','LATEST_PREGAME','LATEST_OBSERVED','RETAINED_OBSERVED'}.issubset({r['horizon'] for r in rows}))
        self.assertTrue(any(r['available'] and r.get('value') is None and r.get('direction') for r in rows))
        recovered=[r for r in rows if r['game_id']=='2026_09_JAX_BAL' and r['provider'] in ['Kalshi','Polymarket'] and r['available'] and r['horizon'] in ['T1','T2','LATEST_PREGAME']]
        self.assertGreaterEqual(len(recovered),18)
        self.assertTrue(all(not r['eligible'] for r in recovered))
    def test_tie_is_retained_and_not_binary_scored(self):
        g=self.games['2026_05_NYG_WAS'];self.assertTrue(g['completed']);self.assertEqual(g['actual']['total'],54);self.assertFalse(g['frozen_binary_benchmark'])
        self.assertTrue(g['frozen_point_benchmark'])
    def test_no_reporting_execution_credit(self):
        for k in ['new_owner_fits','new_owner_issues','new_source_acquisitions']:self.assertEqual(self.data[k],0)
        self.assertFalse(self.data['original_evidence_modified']);self.assertEqual(self.data['next']['actual_owner_results'],0)
        self.assertEqual(len(self.data['correction_comparisons']),255)
        self.assertGreater(self.data['correction_summary'][0]['delta'],0)
    def test_completed_window_census_stays_unchanged(self):
        source=self.data['source_diagnostics'];self.assertEqual(source['registered_games'],121);self.assertEqual(source['feature_rows'],172373);self.assertEqual(source['expanded_window_rows'],689492);self.assertFalse(source['completed_study_recomputed'])
        for m in [1,3,5,10]:
            c=source['minute_window_census'];self.assertEqual(c[f'window_{m}_complete']+c[f'window_{m}_censored'],172373)
    def test_conditional_orientation_and_existing_component_clocks(self):
        rows=self.data['conditional_rows'];self.assertEqual(len(rows),82);self.assertEqual(sum('LESS' in r['orientation'] for r in rows),48);self.assertEqual(sum('GREATER' in r['orientation'] for r in rows),34)
        current=[r for r in self.data['model_rows'] if r['lane_id'].startswith('n052_') and r['available']]
        self.assertEqual(len(current),336);self.assertTrue(all(r.get('fit_completed_at') and r.get('maximum_training_label_available_at') for r in current))
    def test_available_and_eligible_counts_recompute(self):
        for c in self.data['coverage_rows']:
            rows=[r for r in self.data['provider_rows'] if r['provider']==c['provider'] and r['target']==c['target'] and r['horizon']==c['horizon'] and self.games[r['game_id']]['completed']]
            self.assertEqual(len(rows),122);self.assertEqual(sum(r['available'] for r in rows),c['available']);self.assertEqual(sum(r['eligible'] for r in rows),c['eligible'])
    def test_no_wagering_vocabulary_on_active_surfaces(self):
        for file in ['season_review_n053r1.template.html','season_review_n053r1.html','README.md','SEASON_REVIEW_N053R1.md']:
            self.assertIsNone(RETIRED.search(re.sub(r'<script id="nfl-season-payload"[^>]*>.*?</script>','',(HERE/file).read_text(),flags=re.S)),file)
    def test_lossless_deterministic_compressed_data(self):
        import gzip
        raw=(HERE/'current_season_n053r1.json.gz').read_bytes();self.assertEqual(raw,pack(self.data));self.assertEqual(json.loads(gzip.decompress(raw)),self.data);self.assertLess(len(raw),8_000_000)
    def test_deterministic_generation(self):
        self.assertEqual(build(self.data),(HERE/'season_review_n053r1.html').read_text())
    def test_no_fabricated_absent_output(self):
        d=copy.deepcopy(self.data);r=next(r for r in d['model_rows'] if not r['available']);r['value']=.75
        with self.assertRaisesRegex(ValueError,'fabricated absent'):validate(d)
    def test_postgame_issue_rejected(self):
        d=copy.deepcopy(self.data);r=next(r for r in d['model_rows'] if r.get('actual_issue_eligible') and self.games[r['game_id']]['completed']);r['issued_at']='2027-01-01T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError,'postgame'):validate(d)
    def test_future_information_after_issue_rejected(self):
        d=copy.deepcopy(self.data);r=next(r for r in d['model_rows'] if r.get('actual_issue_eligible'));r['feature_asof']='2027-01-01T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError,'information clock'):validate(d)
    def test_full_grid_missing_row_rejected(self):
        d=copy.deepcopy(self.data);d['provider_rows'].pop()
        with self.assertRaisesRegex(ValueError,'complete grid'):validate(d)
    def test_provider_denominator_shrink_rejected(self):
        d=copy.deepcopy(self.data);d['coverage_rows'][0]['denominator']=91
        with self.assertRaisesRegex(ValueError,'denominator'):validate(d)
    def test_private_data_rejected(self):
        d=copy.deepcopy(self.data);d['private']='s3://private-example/object'
        with self.assertRaisesRegex(ValueError,'private publication'):validate(d)
    def test_direction_only_not_fabricated_probability(self):
        d=copy.deepcopy(self.data);r=next(r for r in d['provider_rows'] if r['available'] and r.get('value') is None and r.get('direction'))
        self.assertNotIn('pick_probability',r)
    def test_historical_lanes_remain_reconstruction(self):
        for lane in ['selected_annual','selected_weekly','selected_event']:
            rows=[r for r in self.data['model_rows'] if r['lane_id']==lane and r['available']]
            self.assertEqual(len(rows),360);self.assertTrue(all(not r.get('actual_issue_eligible') for r in rows))

if __name__=='__main__':unittest.main()
