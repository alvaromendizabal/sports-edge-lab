"""Public partial-owner facts, private boundary and exact preservation gates."""
from pathlib import Path
import hashlib,json,re,unittest
from b063r5_status import strip_banner as strip_latest_banner
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/ncaa';EX=ROOT/'examples/ncaa_review'
def git_blob(body):return hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
def strict(body):
 def pairs(items):
  result={}
  for key,value in items:
   if key in result:raise ValueError('Duplicate public field')
   result[key]=value
  return result
 return json.loads(body,object_pairs_hook=pairs)
class B063R4PublicStatus(unittest.TestCase):
 def setUp(self):self.data=strict((DOC/'data/B063R4_PUBLIC_STATUS.json').read_text())
 def test_partial_fit_and_contract_counts_are_distinct(self):
  a=self.data['latest_attempt']
  self.assertEqual((a['authenticated_prior_target_fits'],a['authenticated_content_objects']),(22,134))
  self.assertEqual((a['new_distinct_checkpoint_contracts'],a['reused_distinct_checkpoint_contracts'],a['total_distinct_checkpoint_contracts']),(167,248,415))
  self.assertEqual(a['checkpoint_close_events'],438);self.assertFalse(a['checkpoint_events_are_fit_counts'])
  self.assertFalse(a['terminal_return_verified']);self.assertFalse(a['whole_run_completed'])
  self.assertEqual(a['new_fits_in_this_preparation'],0)
 def test_recorded_resources_do_not_become_acceptance(self):
  a=self.data['latest_attempt'];p=self.data['prepared_continuation']
  self.assertEqual(a['peak_recorded_cpu_cores'],2.9286481116162077)
  self.assertFalse(a['twelve_core_acceptance_proven']);self.assertFalse(a['callbacks_prove_simultaneous_scientific_fits'])
  self.assertFalse(p['owner_execution_verified']);self.assertFalse(p['live_owner_shutdown_observed_in_preparation'])
  self.assertFalse(p['engineering_tests_are_owner_performance'])
  self.assertEqual(p['scientific_identity_families_preserved'],8)
  self.assertEqual(p['new_preparation_scientific_fits'],0)
  self.assertTrue(all(9.9<x<10.1 for x in p['independent_observer_real_sample_intervals_seconds']))
 def test_missing_metrics_clocks_and_provider_gaps_remain_explicit(self):
  a=self.data['latest_attempt'];m=self.data['metric_policy'];p=self.data['publication']
  self.assertEqual(a['last_observed_event_at'],'2026-11-12T23:34:23.600590+00:00')
  self.assertEqual(m['metrics'],['accuracy','log_loss','brier','margin_mae','margin_rmse','total_mae','total_rmse'])
  self.assertIsNone(m['new_scores']);self.assertFalse(m['current_season_complete'])
  self.assertFalse(m['rolling_or_original_issue_promotion']);self.assertFalse(m['missing_quotes_fabricated'])
  self.assertFalse(p['source_publication_is_deployment']);self.assertFalse(p['website_deployment_verified'])
  self.assertFalse(p['provider_refresh_performed'])
 def test_original_landing_game_and_metric_bytes_are_exactly_preserved(self):
  body=strip_latest_banner((DOC/'index.html').read_text()).encode();start=b'<!-- B063R4_PARTIAL_OWNER_STATUS_START -->';end=b'<!-- B063R4_PARTIAL_OWNER_STATUS_END -->\n'
  self.assertEqual(body.count(start),1);self.assertEqual(body.count(end),1)
  left,remaining=body.split(start);_,right=remaining.split(end)
  self.assertEqual(git_blob(left+right),self.data['source_attribution']['preserved_git_blobs']['docs/ncaa/index.html'])
 def test_original_readme_and_browser_contract_are_preserved(self):
  body=(EX/'README.md').read_bytes().split(b'<!-- B063R5_STATUS_END -->\n\n',1)[1];marker=b'<!-- B063R4_STATUS_END -->\n\n'
  self.assertTrue(body.startswith(b'<!-- B063R4_STATUS_START -->'))
  self.assertEqual(git_blob(body.split(marker)[1]),self.data['source_attribution']['preserved_git_blobs']['examples/ncaa_review/README.md'])
  body=(EX/'test_dashboard_browser.cjs').read_bytes().replace(b"    counts.b063r5Status = await require('./test_b063r5_status_browser.cjs').verifyR5(browser, path.join(root, 'docs/ncaa/b063r5.html'));\n",b'');line=b"    counts.b063r4Status = await require('./test_b063r4_status_browser.cjs').verifyR4(browser, path.join(root, 'docs/ncaa/b063r4.html'));\n"
  self.assertEqual(body.count(line),1)
  self.assertEqual(git_blob(body.replace(line,b'')),self.data['source_attribution']['preserved_git_blobs']['examples/ncaa_review/test_dashboard_browser.cjs'])
 def test_standalone_page_contains_exact_downloadable_evidence(self):
  body=(DOC/'b063r4.html').read_text();embedded=re.search(r'<script id="b063r4-data" type="application/json">(.*?)</script>',body,re.S)
  self.assertIsNotNone(embedded);self.assertEqual(strict(embedded.group(1)),self.data)
  self.assertIn('2,454,853,413 bytes',body);self.assertIn('147 identical chunks',body)
  self.assertIn('old owner terminal return is not promised',body)
  self.assertEqual(body.count('<tr><th scope="row">'),len(self.data['repairs']))
  self.assertIn('data/B063R4_PUBLIC_STATUS.json',body)
  self.assertIn(self.data['prepared_continuation']['source_sha256'],body)
 def test_canonical_generation_is_exact_and_banner_is_idempotent(self):
  import b063r4_status as status
  self.assertEqual(status.render_page(),(DOC/'b063r4.html').read_text())
  self.assertEqual(status.load_payload(),self.data)
  landing=strip_latest_banner((DOC/'index.html').read_text());self.assertEqual(status.render_banner(landing),landing)
  self.assertEqual(status.status_outputs({DOC/'index.html':status.strip_banner(landing)})[DOC/'index.html'],landing)
 def test_prepared_and_partial_population_mutations_are_rejected(self):
  import copy,b063r4_status as status
  from unittest.mock import patch
  for category,key,value in [('latest_attempt','terminal_return_verified',True),('latest_attempt','authenticated_prior_target_fits',23),('prepared_continuation','new_preparation_scientific_fits',22),('metric_policy','new_scores',{'accuracy':1})]:
   changed=copy.deepcopy(self.data);changed[category][key]=value
   with patch.object(status.json,'loads',return_value=changed):
    with self.assertRaises(ValueError):status.load_payload()
 def test_new_public_material_excludes_private_runtime_and_cloud_identifiers(self):
  # Inspect only the new publication; dated pre-existing text keeps its own policy.
  text=(DOC/'b063r4.html').read_text()+(DOC/'data/B063R4_PUBLIC_STATUS.json').read_text()
  for forbidden in [r'arn:aws:',r's3://',r'/home/sagemaker',r'AKIA[A-Z0-9]{16}',r'ASIA[A-Z0-9]{16}',r'BEGIN (?:RSA |OPENSSH )?PRIVATE KEY',r'\b(?:worker_pid|frontend_pid|account_id|model_body)\b',r'\.pyz(?:\b|["\'])']:
   self.assertIsNone(re.search(forbidden,text),forbidden)
if __name__=='__main__':unittest.main()
