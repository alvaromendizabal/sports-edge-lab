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

if __name__=='__main__':unittest.main()
