"""Check original issue boundaries and truthful recovered-science rendering."""
import copy
from datetime import datetime
import json
import re
import unittest
import terminal_dashboard as dashboard

class TerminalEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data,cls.raw=dashboard.load_payload()

    def test_native_issue_clock_outcome_and_role_mutations_fail(self):
        for field,value in [('server_last_modified_utc','2030-01-01T00:00:00Z'),('actual',1),('automatic_promotion',True),('durable_issued_before_cutoff',False)]:
            d=copy.deepcopy(self.data)
            next(r for r in d['issues'] if r['display_evidence_mode']=='recovered_native_original')[field]=value
            with self.assertRaises(ValueError):dashboard.validate(d)
        equal=copy.deepcopy(self.data)
        row=next(r for r in equal['issues'] if r['display_evidence_mode']=='recovered_native_original')
        row['server_last_modified_utc']=row['cutoff_time']
        with self.assertRaises(ValueError):dashboard.validate(equal)

    def test_selected_original_closure_and_unchanged_prior(self):
        latest=[r for r in self.data['issues'] if r['display_evidence_mode']=='recovered_native_original']
        self.assertEqual(len({r['issue_record_sha256'] for r in latest}),46)
        self.assertEqual(sum(r['league']=='ncaam' for r in latest),36)
        self.assertEqual(sum(r['target']=='win' for r in latest),16)
        prior=json.loads((dashboard.HERE/'B063_PUBLIC_DATA.json').read_text())['issued_archive']['records']
        rows=[r for r in self.data['issues'] if r['display_evidence_mode']=='preserved_prior_original']
        for before,after in zip(prior,rows,strict=True):
            for k,v in before.items():
                self.assertEqual(round(float(v),6 if before['target']=='win' else 3) if k=='prediction' else v,after[k])

    def test_replay_is_settled_and_unissued(self):
        gcols=self.data['game_columns'];rcols=self.data['replay_columns']
        games=[dict(zip(gcols,r)) for r in self.data['games']]
        key=lambda r:(r['league'],r['event_id'],datetime.fromisoformat(r['event_time']).timestamp())
        bykey={key(g):g for g in games if g['event_time'] and ('+' in g['event_time'] or g['event_time'].endswith('Z'))}
        for row in self.data['replay']:
            r=dict(zip(rcols,row));self.assertTrue(bykey[key(r)]['completed'])
            self.assertIn(r['forecast_status'],['RETROSPECTIVE_NOT_AS_ISSUED','B062_EXPOSED_METRIC_ROLE_RECONSTRUCTION'])
        self.assertNotIn('issued_at',rcols)

    def test_report_cannot_promote_or_assert_owner_runtime(self):
        for k in ['new_dashboard_fits','new_dashboard_issues','promotions','b063_owner_execution_verified','b063_parallelism_on_owner_verified','full_catalog_complete']:
            d=copy.deepcopy(self.data);d['execution'][k]=1
            with self.assertRaises(ValueError):dashboard.validate(d)
        self.assertEqual(self.data['inspected_comparison']['combined_numeric_win_counts'],{'core':2,'retained':12,'tie':0})

    def test_public_boundary_and_escaped_self_contained_render(self):
        for marker in ['s3://','sagemaker-user','access_key','secret_key','api_key','s3_bucket','checkpoint_path','model_weights','feature_columns','B032_errors_and_interactions','B056_native_']:
            self.assertNotIn(marker,self.raw)
        page=dashboard.render('<html><head></head><body><main><p>Earlier science</p></main></body></html>')
        self.assertIn('Earlier science',page);self.assertIn('terminal-archive',page)
        data=re.search(r'<script id="terminal-data" type="application/json">(.*?)</script>',page,re.S)
        self.assertEqual(json.loads(data.group(1)),self.data)
        self.assertNotRegex(page,r'<script[^>]+src=')
        self.assertNotIn('__TERMINAL_',page)

if __name__=='__main__':unittest.main()
