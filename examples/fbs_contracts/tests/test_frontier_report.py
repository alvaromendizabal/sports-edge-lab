"""Public report contracts: full populations, typed missingness and safe exports."""
import json
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(os.environ.get('FBS_REVIEW_ROOT', Path(__file__).resolve().parents[3]))
PUBLIC = Path(os.environ.get('FBS_PUBLIC_DIR', ROOT/'docs/fbs'))

class FrontierReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.transport=json.loads((PUBLIC/'frontier-games.json').read_text())
        cls.rows=[dict(zip(cls.transport['columns'],r)) for r in cls.transport['rows']]

    def test_complete_unique_observed_population(self):
        self.assertEqual(len(self.rows),888)
        self.assertEqual(len({r['game_id'] for r in self.rows}),888)
        self.assertEqual(sum(r['completed'] for r in self.rows),627)
        self.assertEqual(sum(r['replay_p_home'] is not None for r in self.rows),622)

    def test_no_issuance_or_stake_is_invented(self):
        self.assertTrue(all(r['genuine_original_issue_at'] is None for r in self.rows))
        self.assertTrue(all(r['stake_usd']==0 and r['decision']=='NO BET' for r in self.rows))
        self.assertTrue(all(r['spread_cover_probability'] is None for r in self.rows))

    def test_two_source_revisions_preserved(self):
        revisions=self.transport['schedule_revisions']
        self.assertEqual({r['game_id'] for r in revisions},{'401866461','401862840'})
        by={r['game_id']:r for r in self.rows}
        for revision in revisions:
            r=by[revision['game_id']]
            self.assertEqual(r['previous_schedule_kickoff_utc'],revision['old_kickoff'])
            self.assertEqual(r['kickoff_utc'],revision['new_kickoff'])

    def test_midpoints_do_not_replace_point_bounds(self):
        seen=0
        for row in self.rows:
            for provider in ('Kalshi','Polymarket US','Polymarket Global'):
                for target in ('margin','total'):
                    text=row.get(f'{provider}_{target}_point_support')
                    if text:
                        point=json.loads(text)
                        if point.get('method')=='CAPTURED_BID_ASK_HALF_PROBABILITY_SUPPORT':
                            self.assertIsNone(row[f'{provider}_{target}_value'])
                            seen+=1
        self.assertGreater(seen,0)

    def test_latest_owner_and_local_work_remain_distinct(self):
        review=json.loads((PUBLIC/'frontier-review.json').read_text())
        owner=review['owner']; local=review['new_local_source_review']
        self.assertEqual((owner['release'],owner['exit']),('V034',2))
        self.assertEqual((owner['provider_requests'],owner['model_fits'],owner['forecast_issues']),(0,0,0))
        self.assertEqual(owner['research_disk_reserve_bytes']+owner['work_headroom_bytes']-owner['final_free_disk_bytes'],owner['disk_shortfall_bytes'])
        self.assertEqual(local['new_predictive_fits'],0)
        self.assertFalse(local['prior_study_refitted'])
        self.assertEqual(local['prior_predictive_fits_preserved'],33)

    def test_unbound_slots_do_not_inflate_game_population(self):
        review=json.loads((PUBLIC/'frontier-review.json').read_text())
        schedule=review['new_local_source_review']['schedule']
        self.assertEqual(len(schedule['slots']),10)
        self.assertEqual(len(self.rows),888)
        self.assertTrue(all(s['home_team'] is None and s['away_team'] is None and not s['join_eligible'] for s in schedule['slots']))
        self.assertEqual(schedule['calendar_interval_conflicts_count'],1)

    def test_availability_unknowns_and_clocks_are_preserved(self):
        data=json.loads((PUBLIC/'frontier-review.json').read_text())['new_local_source_review']['availability']
        self.assertEqual(sum(data['identity_states'].values()),data['public_report_rows'])
        self.assertEqual(data['players_with_observed_usage']+data['players_without_observed_usage'],data['public_report_rows'])
        self.assertEqual(data['clock_qualified_team_rows_by_horizon'],{'120':58,'60':58})
        self.assertFalse(data['estimated_player_effects_available'])
        self.assertFalse(data['historical_pregame_certification'])
        self.assertEqual(data['new_predictive_fits'],0)

    def test_javascript_filtering_and_csv_failure_cases(self):
        code=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const path=process.argv[1],api=require(path+'/frontier.js'),t=JSON.parse(fs.readFileSync(path+'/frontier-games.json'));
const rows=api.unpack(t),state={query:'',week:'all',window:'all'};
assert.equal(api.filter(rows,state,t.windows).length,888);
assert.equal(api.filter(rows,{...state,window:'previous'},t.windows).length,56);
assert.equal(api.filter(rows,{...state,window:'current'},t.windows).length,63);
assert.equal(api.filter(rows,{...state,week:'14'},t.windows).length,0);
assert.equal(api.filter(rows,{...state,query:'unobserved-team-token'},t.windows).length,0);
assert.throws(()=>api.unpack({columns:['game_id'],rows:[['x'],['x']]}),/Duplicate/);
assert.throws(()=>api.unpack({columns:['game_id'],rows:[['x','extra']]}),/width/);
assert.throws(()=>api.unpack({columns:['game_id','game_id'],rows:[]}),/Invalid/);
assert.match(api.csv([{value:'=1+1'}],['value']),/'=1\+1/);
assert.match(api.csv([{value:null}],['value']),/\r\n""\r\n$/);
"""
        result=subprocess.run(['node','-e',code,str(PUBLIC)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
