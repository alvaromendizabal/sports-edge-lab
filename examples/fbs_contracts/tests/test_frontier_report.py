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
