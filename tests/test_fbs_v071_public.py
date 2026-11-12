"""Verify actual V070 publication, clocks, scope and independent gaps."""
from collections import Counter
from datetime import datetime
from pathlib import Path
import csv, hashlib, io, json, re, runpy, unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/fbs'
def dt(x):return datetime.fromisoformat(x.replace('Z','+00:00'))
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

class ActualV070Publication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(P/'latest-v071.json').read_text()
        cls.d=json.loads(cls.raw)
        cls.games=cls.d['games']

    def test_actual_work_reconciles_completed_failed_and_unattempted(self):
        r=self.d['run_counts'];s=self.d['refresh']
        self.assertEqual((r['new_model_fits'],r['new_rolling_fits'],r['new_genuine_forecasts'],r['new_prediction_outputs']),(1,1,104,312))
        self.assertEqual(r['runtime_exit_code'],2)
        self.assertEqual(s['eligible_tasks'],s['completed_current_origin_issues']+s['failed_tasks']+s['unattempted_tasks'])
        self.assertEqual((s['failed_tasks'],s['unattempted_tasks'],s['total_not_refreshed']),(1,38,39))
        self.assertFalse(self.d['parallel_work']['broad_parallel_fit_stage_reached'])
        self.assertIsNone(self.d['parallel_work']['measured_12_core_throughput_this_run'])

    def test_inventory_preserves_unresolved_and_completed_without_inventing_issues(self):
        self.assertEqual(len(self.games),2742)
        self.assertEqual(len({(g['season'],g['id']) for g in self.games}),2742)
        self.assertEqual(Counter(g['season'] for g in self.games),{2024:920,2025:934,2026:888})
        current=[g for g in self.games if g['season']==2026]
        self.assertEqual(sum(g['completed'] for g in current),691)
        self.assertEqual(sum(not g['kickoff'] for g in current),54)
        self.assertEqual(sum(bool(g['latest']) for g in current),104)
        self.assertEqual(sum(bool(g['saved']) for g in current),141)
        self.assertEqual(sum(bool(g['saved']) and not g['completed'] for g in current),135)
        self.assertEqual(sum(bool(g['recovered_original']) for g in current),55)
        revision=next(g for g in current if g['id']=='401866465')
        self.assertIsNone(revision['latest']);self.assertIsNone(revision['saved'])
        self.assertTrue(all(g['latest'] is None for g in current if not g['kickoff'] or g['completed']))

    def test_issued_clocks_remain_strictly_before_kickoff(self):
        for g in self.games:
            for key in ('latest','saved','recovered_original'):
                x=g[key]
                if x is None:continue
                self.assertLessEqual(dt(x['cutoff_at']),dt(x['issue_at']))
                self.assertLess(dt(x['issue_at']),dt(g['kickoff']))
                self.assertFalse(x['promotion_authorized'])
                self.assertGreaterEqual(x['probability'],0);self.assertLessEqual(x['probability'],1)
                if key=='latest':
                    self.assertLessEqual(dt(x['maximum_information_at']),dt(x['cutoff_at']))
                    self.assertLessEqual(dt(x['cutoff_at']),dt(x['computed_at']))
                    self.assertLessEqual(dt(x['computed_at']),dt(x['issue_at']))
                    self.assertEqual(x['horizon'],'CURRENT_ORIGIN_OUTLOOK')
                if key=='recovered_original':
                    self.assertIsNone(x['margin']);self.assertIsNone(x['total'])

    def test_season_metrics_and_market_denominators_do_not_blend_cohorts(self):
        rows=self.d['annual_leaders']
        self.assertEqual(len(rows),21)
        self.assertEqual(Counter(r['season'] for r in rows),{2024:7,2025:7,2026:7})
        self.assertEqual({r['games'] for r in rows if r['season']==2026},{688})
        ll=next(r for r in rows if (r['season'],r['metric'])==(2026,'log_loss'))
        self.assertAlmostEqual(ll['value'],0.5409218605468924,places=12)
        self.assertEqual(self.d['separate_685_catboost_winner']['games'],685)
        self.assertEqual({r['games'] for r in self.d['separate_301_leaders']},{301})
        self.assertEqual({r['cohort_games'] for r in self.d['separate_231_comparison']},{231})
        prov=self.d['provider_qualified_cohorts']
        self.assertEqual(len(prov),12)
        self.assertEqual({(r['season'],r['provider']) for r in prov},{(y,p) for y in (2024,2025,2026) for p in self.d['provider_names']})
        for r in prov:
            self.assertEqual((r['official_games'],r['completed_games']),{2024:(920,919),2025:(934,934),2026:(888,691)}[r['season']])
            self.assertEqual([r[k] for k in ('qualified_winner_games','qualified_margin_games','qualified_total_games','qualified_cover_games')],[0,0,0,0])

    def test_embedded_report_and_selected_csv_are_exact_public_projection(self):
        html=(P/'latest-v071.html').read_text()
        embedded=re.search(r'<script id="report-data" type="application/json">(.*?)</script>',html,re.S).group(1)
        self.assertEqual(json.loads(embedded),self.d)
        rows=list(csv.DictReader(io.StringIO((P/'issued-v070-selected.csv').read_text())))
        self.assertEqual(len(rows),104)
        by={g['id']:g for g in self.games if g['latest']}
        self.assertEqual({r['game_id'] for r in rows},set(by))
        for r in rows:
            x=by[r['game_id']]['latest']
            self.assertEqual(float(r['home_probability']),x['probability'])
            self.assertEqual(r['issue_at_utc'],x['issue_at'])
        self.assertEqual(len(list(csv.DictReader(io.StringIO((P/'season-inventory-v071.csv').read_text())))),2742)

    def test_public_boundary_and_source_truth(self):
        forbidden={'model_id','model_sha256','model_snapshot_sha256','recipe','recipe_id','recipe_policy_sha256','feature_names','weights','bucket','s3_key','credentials','api_key','raw_quotes','promotion_thresholds','promotion_support'}
        def visit(v):
            if isinstance(v,dict):
                self.assertFalse(set(v)&forbidden)
                for val in v.values():visit(val)
            elif isinstance(v,list):
                for val in v:visit(val)
            elif isinstance(v,str):self.assertNotRegex(v,r's3://|arn:aws:|/home/sagemaker-user|/sports-edge-lab/shared/|\b(?:betting|wager|bankroll|stake|ROI)\b')
        visit(self.d)
        self.assertFalse(self.d['champions']['current_owner_selection_reached'])
        self.assertFalse(self.d['champions']['publication_is_promotion'])
        self.assertFalse(self.d['publication']['metrics_rescored_from_public_values'])
        for g in self.games:
            self.assertNotIn('reconstruction_p_home',g)
            self.assertEqual(len(g['providers']),4)
            self.assertTrue(all(len(c)==4 for c in g['providers']))
        self.assertEqual(self.d['source_owner_return_sha256'],'c3930f3f098ce41c8193dcccb9e38240806eda4ec398ee869bc1ca4b83bc69fb')

    def test_prior_landing_content_preserved_outside_latest_link(self):
        for name,sha in [('complete.html','4feef263ab5f1ec44fd2ab21a7aa8c9f8f4273fc'),('current.html','8bfe5b333e8eb448218a79662fadf65bc06e4a2a')]:
            txt=(P/name).read_text()
            txt=re.sub(r'<!-- FBS_V072_LATEST_LINK_START -->.*?<!-- FBS_V072_LATEST_LINK_END -->','',txt,flags=re.S)
            stripped=re.sub(r'<!-- FBS_V071_LATEST_LINK_START -->.*?<!-- FBS_V071_LATEST_LINK_END -->','',txt,flags=re.S)
            self.assertEqual(blob(stripped.encode()),sha)
        txt=(P/'README.md').read_text()
        txt=re.sub(r'<!-- FBS_V072_ACTUAL_V071_START -->.*?<!-- FBS_V072_ACTUAL_V071_END -->\n\n','',txt,flags=re.S)
        stripped=re.sub(r'<!-- FBS_V071_ACTUAL_V070_START -->.*?<!-- FBS_V071_ACTUAL_V070_END -->\n\n','',txt,flags=re.S)
        self.assertEqual(blob(stripped.encode()),'2ec8304db6b43b29667afa8f31997082ad4dd048')

    def test_host_export_contains_current_report_and_keeps_earlier_entrypoints(self):
        export=runpy.run_path(str(ROOT/'examples/fbs_contracts/export_site.py'))
        self.assertEqual(export['SOURCE_FILES']['index.html'],'latest-v072.html')
        self.assertEqual(export['SOURCE_FILES']['season-archive.html'],'index.html')
        for name in ('latest-v071.html','latest-v071.js','latest-v071.css','latest-v071.json','issued-v070-selected.csv','season-inventory-v071.csv','current.html','complete.html'):
            self.assertIn(name,export['ASSETS'])

if __name__=='__main__':unittest.main()
