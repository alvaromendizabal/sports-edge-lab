import json
import math
import unittest
from collections import Counter
from datetime import datetime
from pathlib import Path
from examples.fbs_contracts.build_three_season_review import display_target, PINS

ROOT = Path(__file__).resolve().parents[3]
REPORT = json.loads((ROOT/'docs/fbs/three-season.json').read_text())
ROWS = REPORT['rows']
BY_ID = {r['id']: r for r in ROWS}

class ThreeSeasonReviewTests(unittest.TestCase):
    def test_complete_inventory_and_disjoint_explicit_gaps(self):
        self.assertEqual(len(ROWS), 2742)
        self.assertEqual(len(BY_ID), len(ROWS))
        self.assertEqual(Counter(r['season'] for r in ROWS), {2024:920,2025:934,2026:888})
        self.assertEqual(Counter(r['projection_status'] for r in ROWS), {
            'RECONSTRUCTED_DEVELOPMENT':2403, 'INSUFFICIENT_PRIOR_OUTCOMES':240, 'EXACT_KICKOFF_UNRESOLVED':99})
        self.assertEqual([(r['season'],r['observed_complete']) for r in REPORT['seasons']], [(2024,919),(2025,934),(2026,629)])
        self.assertTrue(all(r['season']==2024 for r in ROWS if r['projection_status']=='INSUFFICIENT_PRIOR_OUTCOMES'))
    def test_placeholder_time_never_becomes_exact_kickoff(self):
        missing=[r for r in ROWS if not r['kickoff_exact']]
        self.assertEqual(len(missing),99)
        self.assertTrue(all(r['kickoff'] is None and not r['models'] for r in missing))
        g=BY_ID['401643703']
        self.assertEqual((g['away'],g['home']),('Robert Morris','Utah State'))
        self.assertEqual(g['reported_kickoff'],'2024-08-31T04:00:00Z')
        self.assertIsNone(g['kickoff'])
        self.assertEqual((BY_ID['401856748']['home_id'],BY_ID['401856748']['away_id']),('57','238'))
    def test_exact_current_inventory_and_prior_values_remain_separate(self):
        d=json.loads((ROOT/'docs/fbs/complete-season.json').read_text())
        original={r[0]:dict(zip(d['columns'],r)) for r in d['rows']}
        self.assertEqual({r['id'] for r in ROWS if r['season']==2026},set(original))
        r=json.loads((ROOT/'docs/fbs/development-2026.json').read_text())
        for row in r['rows']:
            new=BY_ID[row['id']]
            self.assertEqual(new['kickoff'],row['kickoff'])
            self.assertEqual(new['cutoff'],row['cutoff'])
            for family, targets in row['models'].items():
                for target, value in targets.items():
                    self.assertEqual(new['models'][family][target]['prediction'], round(value['prediction'],4 if target=='winner' else 2))
        self.assertEqual(sum(g['period']=='current' and bool(g['models']) for g in ROWS),63)
    def test_ordered_team_identity_and_chronological_cutoffs(self):
        for row in ROWS:
            self.assertTrue(row['home'] and row['away'])
            self.assertTrue(row['home_id'] and row['away_id'])
            self.assertNotEqual(row['home_id'],row['away_id'])
            if row['kickoff_exact']:
                self.assertTrue(row['home_id'] and row['away_id'])
                self.assertNotEqual(row['home_id'],row['away_id'])
                self.assertLess(datetime.fromisoformat(row['cutoff'].replace('Z','+00:00')),datetime.fromisoformat(row['kickoff'].replace('Z','+00:00')))
    def test_saved_individual_intervals_and_no_invented_blend_distribution(self):
        total=0; intervals=0
        for row in ROWS:
            if not row['models']:continue
            self.assertEqual(set(row['models']['fixed_equal_blend']),{'winner','margin','total'})
            for family, targets in row['models'].items():
                for target, value in targets.items():
                    total+=1;self.assertTrue(math.isfinite(value['prediction']))
                    if target=='winner': self.assertTrue(0<=value['prediction']<=1)
                    if 'interval80' in value:
                        intervals+=1
                        self.assertLessEqual(*value['interval80']);self.assertLessEqual(*value['interval95'])
                    if family=='fixed_equal_blend':self.assertNotIn('interval80',value)
                    if target=='margin':self.assertIsNone(value['cover_probability'])
        self.assertEqual(total,33642)
        self.assertEqual(intervals,19224)
    def test_public_field_boundary_and_immutable_source_pins(self):
        for source in REPORT['sources']:
            if source['file'] in PINS:self.assertEqual((source['bytes'],source['sha256']),PINS[source['file']])
        text=json.dumps(REPORT)
        for forbidden in ['s3://','source_reference','feature_names','fit_identity_sha256','model_state_sha256','api_key','raw_bid','stake_usd']:
            self.assertNotIn(forbidden,text)
        for flag in ['forecast_issued','historical_availability_proved','promotion_allowed']:
            self.assertFalse(REPORT[flag])
        for count in ['new_fits','new_provider_requests','new_issues']:self.assertEqual(REPORT[count],0)
    def test_rejects_unadmitted_cover_and_invalid_saved_outputs(self):
        base={'target':'margin','prediction':3.1,'computed_at_utc':'2026-11-07T00:00:00Z'}
        with self.assertRaises(ValueError):display_target({**base,'spread_cover':{'probability':.75}})
        with self.assertRaises(ValueError):display_target({**base,'interval80':[20,-20]})
        with self.assertRaises(ValueError):display_target({**base,'prediction':float('nan')})
        with self.assertRaises(ValueError):display_target({**base,'target':'winner','prediction':1.01})

if __name__=='__main__':unittest.main()
