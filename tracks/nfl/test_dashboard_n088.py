import hashlib
import json
import unittest
from pathlib import Path
import build_dashboard_n088 as dashboard


class PublicDashboardContracts(unittest.TestCase):
    def test_preserves_all_games_and_issue_clocks(self):
        data,_=dashboard.build_payload()
        source=json.loads(dashboard.FORECAST.read_bytes())
        self.assertEqual(len(data['games']),272)
        current=0
        for original,public in zip(source['games'],data['games']):
            self.assertEqual(original['game_id'],public['game_id'])
            self.assertEqual(original['source_observed_at_utc'],public['source_observed_at_utc'])
            for target,panel in original['targets'].items():
                rows=public['targets'][target]['rows']
                for kind in ('current_forecasts','earlier_saved_forward','prior_selected_reconstruction'):
                    recovered=[{k:v for k,v in r.items() if k!='saved_group'} for r in rows if r['saved_group']==kind]
                    self.assertEqual(panel[kind],recovered)
                current+=len(panel['current_forecasts'])
        self.assertEqual(current,444)
        self.assertFalse(data['schedule_refresh_claimed'])

    def test_build_is_deterministic_and_small(self):
        first=dashboard.assets();self.assertEqual(first,dashboard.assets())
        self.assertLess(len(first['index.html']),2_000_000)
        receipt=json.loads(first['publication.json'])
        for name,record in receipt['assets'].items():
            self.assertEqual(hashlib.sha256(first[name]).hexdigest(),record['sha256'])
        self.assertEqual(receipt['new_fits'],0)

    def test_unknown_counts_and_provider_gaps_not_fabricated(self):
        data,_=dashboard.build_payload()
        self.assertIsNone(data['execution']['final_fit_totals'])
        self.assertEqual(data['execution']['verified_completed_new_scientific_receipts'],0)
        for record in data['market_status'].values():
            self.assertEqual(record['new_qualified_comparison_cells'],0)
            self.assertIn('observed pregame-clock',record['reason'])
        self.assertFalse(data['automatic_promotion'])
        self.assertFalse(data['automatic_rolling_refits'])

    def test_scriptless_fallback_and_no_external_scripts(self):
        page=dashboard.assets()['index.html'].decode()
        self.assertIn('<noscript>',page)
        self.assertNotIn('<script src=',page)
        self.assertIn('ARCHIVED REGRESSION REFERENCE',page)
        self.assertEqual(page.split('<noscript>')[1].split('</noscript>')[0].count('<tr>'),273)

    def test_new_phase_a_is_partial_and_public_safe(self):
        data,_=dashboard.build_payload();phase=data['phase_a']
        self.assertEqual(phase['new_fits'],0)
        self.assertFalse(phase['phase_b_admitted'])
        self.assertEqual(phase['status'],'PHASE_A_PARTIAL_EVIDENCE_RECOVERED')
        self.assertTrue(phase['scorecards'])
        self.assertTrue(phase['gaps'])
        self.assertNotIn('cache',phase)
        self.assertNotIn('performance',phase)
        self.assertNotIn('/home/',json.dumps(phase))
        self.assertEqual(sum(g['official_time_tbd'] for g in data['games']),24)
        self.assertTrue(all(g['kickoff_utc'] is None for g in data['games'] if g['official_time_tbd']))
        self.assertTrue(all(r['automatic_promotion'] is False for r in phase['scorecards']))


if __name__=='__main__':unittest.main()
