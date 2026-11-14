"""Portable regression tests for the chronological total blend; fabricated cases only."""
import copy
from datetime import datetime, timezone, timedelta
import unittest
from n095_market_anchor import compute

def samples():
    result=[]
    for year in [2024,2025,2026]:
        for name in ['alpha','beta','gamma']:
            rows=[]
            for week in range(1,8):
                start=datetime(year,1,1,tzinfo=timezone.utc)+timedelta(weeks=week)
                for g in range(10):
                    line=42.5+(g%2); edge=(-3,2,1,-1)[g%4]
                    rows.append(dict(game_id=f'{year}-{week}-{g}',week=week,actual_total=line+edge,point_total=line+edge,total_market_line=line,virtual_origin=start.isoformat(),label_available_at=(start+timedelta(hours=24)).isoformat()))
            result.append(dict(evaluation_rows=rows,model_version=name+str(year),family=name,season=year))
    return result

class TimeValidity(unittest.TestCase):
    def test_registered_protocol(self):
        r=compute(samples())
        self.assertEqual(r['statistical_weekly_estimates'],3*3*4)
        self.assertEqual(len(r['rows']),360)
        self.assertTrue(all(f['latest_label']<f['origin'] and f['n']>=24 and 0<=f['weight']<=1 for f in r['fits']))
        self.assertTrue(all(v['mae']['blend']<v['mae']['market'] for v in r['weighted']))
        self.assertTrue(all(v['mae']['negative']>v['mae']['market'] for v in r['weighted']))
    def test_post_origin_mutation(self):
        s=samples(); before=compute(s)
        for t in s:
            for r in t['evaluation_rows']:
                if r['week']==7:r['actual_total']+=99
        self.assertEqual(before['fits'],compute(s)['fits'])
    def test_late_record_and_duplicates(self):
        s=samples()
        for t in s:
            for r in t['evaluation_rows']:
                if r['week']<=3:r['label_available_at']='2030-01-01T00:00:00+00:00'
        self.assertTrue(all(f['week']>=7 for f in compute(s)['fits']))
        s[0]['evaluation_rows'].append(s[0]['evaluation_rows'][0])
        with self.assertRaises(ValueError):compute(s)
if __name__=='__main__':unittest.main()
