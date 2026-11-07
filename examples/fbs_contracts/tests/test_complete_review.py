import json
import unittest
from pathlib import Path
from examples.fbs_contracts.build_complete_review import EXPECTED_BYTES, EXPECTED_SHA256

ROOT=Path(__file__).resolve().parents[3]
D=json.loads((ROOT/'docs/fbs/complete-season.json').read_text())
G=[dict(zip(D['columns'],r)) for r in D['rows']]
BY_ID={g['id']:g for g in G}

class CompleteReviewTests(unittest.TestCase):
    def test_complete_capture_and_periods(self):
        self.assertEqual(len(BY_ID),888)
        self.assertEqual(sum(g['completed'] for g in G),629)
        self.assertEqual(sum(g['replay_p_home'] is not None for g in G),622)
        self.assertEqual([(p,sum(g['period']==p for g in G),sum(g['period']==p and g['completed'] for g in G)) for p in ['previous','current']],[('previous',56,56),('current',63,7)])
        self.assertTrue(all(g['replay_p_home'] is None for g in G if g['period']=='current'))
        self.assertEqual(D['source_report_bytes'],EXPECTED_BYTES)
        self.assertEqual(D['source_report_sha256'],EXPECTED_SHA256)
    def test_final_reconciliation_and_schedule_quarantine(self):
        for game_id,away,home in [('401862817',29,60),('401869964',54,23)]:
            g=BY_ID[game_id];self.assertEqual((g['away_score'],g['home_score']),(away,home));self.assertTrue(g['completed']);self.assertIsNone(g['replay_p_home'])
        quarantines={g['id'] for g in G if 'QUARANTINED' in g['schedule_join']}
        self.assertEqual(quarantines,{'401864542','401864546'})
        self.assertEqual(BY_ID['401864542']['kickoff'],'2026-11-21T02:00:00Z')
        self.assertEqual(BY_ID['401864546']['kickoff'],'2026-11-27T21:30:00Z')
        self.assertEqual(D['metadata']['unbound_championship_slots'],10)
        self.assertTrue(D['metadata']['army_navy_native_week_conflict'])
    def test_source_and_model_clocks_remain_separate(self):
        self.assertEqual(D['source_observed_at'],'2026-11-06T20:28:52Z')
        self.assertEqual(D['capture_completed_at'],'2026-11-06T20:29:25Z')
        self.assertNotEqual(D['source_observed_at'],D['retained_model_report_at'])
        self.assertEqual(D['counts']['genuine_rolling_forecasts'],0)
        self.assertEqual(D['metadata']['historical_possession_verified'],0)
    def test_providers_and_point_intervals_are_not_collapsed(self):
        self.assertEqual([sum(g[p+'_winner_value'] is not None for g in G) for p in D['providers']],[600,708,680,702])
        for t in ['margin','total']:
            self.assertEqual(sum(g['Polymarket US_'+t+'_value'] is not None for g in G),0)
            self.assertEqual(sum(bool(g['Polymarket US_'+t+'_point_support']) for g in G),52)
        self.assertTrue(all(g['cover_status']=='UNAVAILABLE_NO_QUALIFIED_COVER_PROBABILITY' for g in G))
        self.assertTrue(all(g['replay_total'] is None for g in G if g['replay_p_home'] is None))
    def test_public_projection_excludes_private_fields(self):
        text=(ROOT/'docs/fbs/complete-season.json').read_text()
        for forbidden in ['s3://','sagemaker-sports-edge-lab','source_reference','access_token','api_key','stake_usd','decision_reason','raw_bid']:
            self.assertNotIn(forbidden,text)
        self.assertEqual(len(D['columns']),len(set(D['columns'])))
        self.assertTrue(all(len(r)==len(D['columns']) for r in D['rows']))
    def test_retained_metric_history_is_not_recalculated(self):
        history=(ROOT/'docs/fbs/complete-history.js').read_text()
        h=json.loads(history.split('=',1)[1].removesuffix(';\n'))
        source=json.loads((ROOT/'docs/fbs/model-registry.json').read_text())
        self.assertEqual(h['registry'],source)
        self.assertEqual(len(source['rows']),358)
        self.assertEqual(len({r['model_id'] for r in source['rows']}),167)
        original=json.loads((ROOT/'docs/fbs/common-game-review.json').read_text())
        for new,old in zip(h['common']['cohorts'],original['cohorts']):
            self.assertEqual(new['metrics'],old['metrics']);self.assertEqual(new['identity_sha256'],old['identity_sha256'])
        self.assertEqual(D['replay_headline']['games'],622)
        self.assertEqual(D['replay_headline']['correct'],465)
        self.assertEqual(D['replay_headline']['log_loss'],0.5133276378012555)

class DevelopmentReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads((ROOT/'docs/fbs/development-2026.json').read_text())
    def test_every_known_kickoff_and_current_week_has_three_targets(self):
        r=self.r;ids={x['id'] for x in r['rows']}
        self.assertEqual(len(ids),790);self.assertEqual(len(r['unresolved']),98)
        self.assertEqual(ids|{x['id'] for x in r['unresolved']},set(BY_ID))
        self.assertEqual(sum(BY_ID[x]['period']=='current' for x in ids),63)
        for row in r['rows']:
            self.assertEqual(row['kickoff'],BY_ID[row['id']]['kickoff'])
            self.assertLess(row['cutoff'],row['kickoff'])
            self.assertEqual(set(row['models']['fixed_equal_blend']),{'winner','margin','total'})
            self.assertTrue(0<=row['models']['fixed_equal_blend']['winner']['prediction']<=1)
    def test_reconstruction_is_separate_and_sources_are_pinned(self):
        r=self.r
        self.assertFalse(r['forecast_issued']);self.assertFalse(r['historical_availability_proved']);self.assertFalse(r['promotion_allowed'])
        self.assertEqual(r['default_family'],'fixed_equal_blend')
        self.assertEqual(r['sources'][0]['sha256'],'e7355603e26518de437456f30f7011573f2847f24fe4aa8234628caee886dcb2')
        self.assertEqual(r['sources'][0]['bytes'],2039312)
        self.assertEqual(r['schedule_observed_at'],'2026-11-06T20:28:52Z')
        self.assertEqual(r['computed_at'],'2026-11-07T01:51:51.403891Z')
        self.assertEqual({x['games'] for x in r['metrics']['2026']},{629})
        self.assertEqual({x['games'] for x in r['metrics']['current_week']},{7})
        self.assertEqual({x['games'] for x in r['metrics']['2024']},{678})
        self.assertEqual({x['games'] for x in r['metrics']['2025']},{934})
        self.assertEqual(len(r['metrics']['2025']),14)
        self.assertEqual(r['cumulative_work']['total_successful_base_plus_calibration_fits'],3178)
        self.assertEqual(r['cumulative_work']['compatible_fit_state_reuses'],1232)
        self.assertEqual(r['cumulative_work']['target_outputs'],33642)
        self.assertEqual(r['cumulative_work']['games_with_predictions'],2403)
        self.assertEqual(r['cumulative_work']['unchanged_completed_fit_ids_duplicated'],0)
        self.assertEqual(r['season_coverage'][1]['predicted'],934)
        for forbidden in ['s3://','api_key','state_file','access_token','raw_bid']:
            self.assertNotIn(forbidden,json.dumps(r))

if __name__=='__main__':unittest.main()
