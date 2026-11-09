"""Regression gates for partial native states, new monitored scores and no prior drift."""
import base64,copy,gzip,json,re,unittest
from build_season_review_n054 import HERE,load,build,validate
class PublicN062(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=load()
 def rejects(self,fn):
  d=copy.deepcopy(self.data);fn(d)
  with self.assertRaises(ValueError):validate(d)
 def test_actual_work_keeps_separate_units(self):
  o=self.data['n062_owner_status'];self.assertEqual([o[k]for k in ['native_starts','optimizer_entries','native_returns','validated_returned_states','durable_native_commits','returned_uncommitted_states']],[6,6,6,6,4,2]);self.assertEqual((o['issue_rows'],o['monitor_evaluations'],o['monitor_games']),(90,405,13));self.assertIsNone(o['aggregate_fit_total']);self.assertIsNone(o['aggregate_issue_total'])
 def test_monitor_closed_population(self):
  o=self.data['n062_owner_status'];self.assertEqual(o['monitor_evaluations']+o['monitor_unsupported_rows']+o['monitor_not_final_rows'],o['monitor_input_rows'])
 def test_all_272_games_and_equal_25_horizon_grid(self):
  d=self.data;self.assertEqual(len(d['games']),272);self.assertEqual(sum(g['completed']for g in d['games']),135);self.assertEqual(sum(len(r['horizons'])for g in d['games']for r in g['source_coverage']),61200);self.assertEqual(d['counts']['private_model_cells'],116688)
 def test_60_new_original_issue_groups_do_not_rewrite_scores(self):
  old=load(HERE/'public_projection_n061.json.gz');self.assertEqual(self.data['scoreboards'][:1289],old['scoreboards']);new=self.data['scoreboards'][1289:];self.assertEqual(len(new),60);self.assertTrue(all(r['study']=='N061 original-issued monitoring'and 1<=r['games']<=13 for r in new));self.assertEqual(self.data['issued_cards'],old['issued_cards'])
 def test_current_html_embeds_exact_payload(self):
  body=(HERE/'season_review_n054.html').read_text();self.assertEqual(body,build(self.data));payload=re.search(r'<script id="nfl-public-payload"[^>]*>([^<]+)</script>',body)[1];self.assertEqual(json.loads(gzip.decompress(base64.b64decode(payload))),self.data);self.assertIn('id="show-original-monitor"',body)
 def test_invented_commit_is_rejected(self):self.rejects(lambda d:d['n062_owner_status'].update(durable_native_commits=6,returned_uncommitted_states=0))
 def test_return_not_new_issue(self):self.rejects(lambda d:d['n062_owner_status'].update(actual_V5_issues=6))
 def test_nulls_cannot_be_repaired(self):self.rejects(lambda d:d['n062_owner_status'].update(aggregate_fit_total=6))
 def test_historical_metrics_immutable(self):self.rejects(lambda d:d['scoreboards'][0].update(games=135))
 def test_monitor_not_405_games(self):self.rejects(lambda d:d['scoreboards'][-1].update(games=405))
 def test_old_quote_clock_immutable(self):self.rejects(lambda d:d['games'][0]['source_coverage'][0]['horizons'][0].update(quote_at='2026-11-09T00:00:00Z'))
 def test_quote_value_not_public(self):self.rejects(lambda d:d['games'][0]['source_coverage'][0]['horizons'][-1].update(value=.7))
 def test_private_active_transform_not_public(self):self.rejects(lambda d:d['v5_scope'].update(feature_columns=['private']))
 def test_no_v5_score_without_evidence(self):self.rejects(lambda d:d['v5_scope']['comparison_lanes'][0].update(log_loss=.4))
 def test_missing_source_is_specific(self):self.assertEqual(self.data['n062_owner_status']['current_source_blocker'],'TEAM_STATS_MISSING_2026_09_TB_CHI')
if __name__=='__main__':unittest.main()
