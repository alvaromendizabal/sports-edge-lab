"""Actual N082 publication contracts, including failed-stage and live-game limits."""
import copy,hashlib,json,re,unittest
from pathlib import Path
import selected_review_n083 as view

ROOT=Path(__file__).resolve().parent
RAW=(ROOT/view.FORECAST).read_bytes()
HEALTH=json.loads((ROOT/view.HEALTH).read_bytes())
DATA=json.loads(RAW)

class ActualN082PublicationTests(unittest.TestCase):
 def render(self,health=None):return view.render(RAW,health or HEALTH)
 def test_exact_original_selected_projection(self):
  self.assertEqual(hashlib.sha256(RAW).hexdigest(),HEALTH['selected_forecasts_sha256'])
  self.assertEqual(DATA['display_cutoff_utc'],'2026-11-13T04:18:31.686021+00:00')
  self.assertEqual(HEALTH['owner_return_sha256'],'b37e0dcabea8de8ae0a1a63f1638111fe9216e628594d02228bc08b9049b465c')
 def test_game_lifecycle_partition(self):
  from datetime import datetime
  cutoff=datetime.fromisoformat(DATA['display_cutoff_utc']);counts=dict(completed=0,live=0,confirmed_future=0,kickoff_tbd=0)
  for g in DATA['games']:
   kind='completed'if g['completed_in_saved_census']else'kickoff_tbd'if g['official_time_tbd']else'live'if datetime.fromisoformat(g['kickoff_utc'])<=cutoff else'confirmed_future'
   counts[kind]+=1
  self.assertEqual(counts,dict(completed=136,live=1,confirmed_future=111,kickoff_tbd=24))
  self.assertEqual(sum(counts.values()),272)
 def test_live_game_has_no_new_pregame_issue(self):
  game=next(g for g in DATA['games']if g['game_id']=='2026_10_WAS_NYG')
  self.assertEqual(game['official_date_status'],'0:48 - 4th Quarter')
  self.assertEqual(game['source_observed_at_utc'],'2026-11-13T04:15:18.318444+00:00')
  self.assertFalse(game['completed_in_saved_census'])
  self.assertTrue(all(not t['current_forecasts']for t in game['targets'].values()))
  self.assertTrue(any(t['earlier_saved_forward']for t in game['targets'].values()))
 def test_unknown_whole_run_counter_preserved(self):
  self.assertIsNone(HEALTH['new_fits']);self.assertIsNone(HEALTH['new_native_fits']);self.assertIsNone(HEALTH['new_meta_fits'])
  self.assertEqual(HEALTH['verified_new_fit_minimum'],337)
  self.assertFalse(HEALTH['owner_research_acceptance'])
 def test_fabricated_global_total_rejected(self):
  d=copy.deepcopy(HEALTH);d['new_fits']=337
  with self.assertRaisesRegex(ValueError,'MINIMUM_AND_UNKNOWN'):self.render(d)
 def test_zero_fit_relabel_rejected(self):
  d=copy.deepcopy(HEALTH);d['verified_new_fit_minimum']=0
  with self.assertRaisesRegex(ValueError,'MINIMUM_AND_UNKNOWN'):self.render(d)
 def test_owner_success_relabel_rejected(self):
  d=copy.deepcopy(HEALTH);d['owner_research_acceptance']=True
  with self.assertRaises(ValueError):self.render(d)
 def test_live_game_misclassified_final_rejected(self):
  d=copy.deepcopy(HEALTH);d['saved_census']['completed']=137;d['saved_census']['live']=0
  with self.assertRaisesRegex(ValueError,'CENSUS'):self.render(d)
 def test_all_new_candidates_and_annual_cards(self):
  cards=HEALTH['new_science']['cards'];self.assertEqual(len(cards),216)
  pairs={(r['model_alias'],r['season'])for r in cards};self.assertEqual(len(pairs),216)
  self.assertEqual(len({r['model_alias']for r in cards}),108)
  self.assertEqual({r['comparison_horizon_seconds']for r in cards},{3600})
  self.assertEqual({r['season']for r in cards},{2024,2025})
  self.assertEqual(len({r['family']for r in cards}),9)
 def test_dropped_candidate_card_rejected(self):
  d=copy.deepcopy(HEALTH);d['new_science']['cards'].pop()
  with self.assertRaisesRegex(ValueError,'CARDS_INCOMPLETE'):self.render(d)
 def test_future_selection_or_horizon_change_rejected(self):
  for key,value in [('season',2026),('comparison_horizon_seconds',7200),('promotion_authorized',True)]:
   with self.subTest(key=key):
    d=copy.deepcopy(HEALTH);d['new_science']['cards'][0][key]=value
    with self.assertRaisesRegex(ValueError,'COHORT_OR_PROMOTION'):self.render(d)
 def test_negative_new_candidate_comparisons_preserved(self):
  rows=HEALTH['new_science']['matched_new_vs_preserved'];self.assertEqual(len(rows),9)
  self.assertTrue(all(r['improvement_over_preserved_best']<=0 for r in rows))
  d=copy.deepcopy(HEALTH);d['new_science']['matched_new_vs_preserved'][0]['improvement_over_preserved_best']=.1
  with self.assertRaisesRegex(ValueError,'SUPERIORITY'):self.render(d)
 def test_prior_roles_remain_exact_dated_evidence(self):
  prior=json.loads((ROOT/'selected_forecasts_n080.json').read_bytes())
  self.assertEqual(HEALTH['previous_selected_roles']['roles'],prior['selected_historical_roles'])
  self.assertEqual(len(prior['selected_historical_roles']),27)
  self.assertEqual({r['comparison_horizon_seconds']for r in prior['selected_historical_roles']},{3600,7200})
 def test_all_current_aggregate_cards_and_former_gaps(self):
  self.assertEqual(len(HEALTH['selected_and_retained_2026_scorecards']),77)
  self.assertEqual(len({r['model_alias']for r in HEALTH['selected_and_retained_2026_scorecards']}),34)
  self.assertEqual(HEALTH['current_2026_reuse']['new_2026_score_cases'],0)
  self.assertEqual(sum(r['included_in_current_export']for r in HEALTH['selected_and_retained_2026_scorecards']),40)
  self.assertEqual(len(HEALTH['former_unresolved_roles']),18)
  self.assertTrue(all(r['comparison_horizon_seconds']is None for r in HEALTH['former_unresolved_roles']))
 def test_current_leaders_exact_target_horizon_cohort(self):
  cards=HEALTH['selected_and_retained_2026_scorecards']
  for row in HEALTH['selected_2026_descriptive_leaders']:
   group=[c for c in cards if (c['target'],c['comparison_horizon_seconds'],c['cohort_sha256'])==(row['target'],row['comparison_horizon_seconds'],row['cohort_sha256'])and row['metric']in c['metrics']]
   self.assertEqual(row['selected_candidates_compared'],len({c['model_alias']for c in group}))
   best=(max if row['metric']=='accuracy'else min)(c['metrics'][row['metric']]for c in group)
   self.assertEqual(row['value'],best)
   self.assertEqual(set(row['model_aliases']),{c['model_alias']for c in group if c['metrics'][row['metric']]==best})
 def test_no_fabricated_provider_comparison(self):
  self.assertEqual(HEALTH['new_qualified_market_comparison_cells'],0)
  self.assertEqual(len(HEALTH['current_replay_comparison_missing']),9)
  d=copy.deepcopy(HEALTH);d['new_qualified_market_comparison_cells']=1
  with self.assertRaisesRegex(ValueError,'MARKET_COMPARISON'):self.render(d)
 def test_source_publication_boundary(self):
  body=RAW.decode()+json.dumps(HEALTH)
  for token in ['/home/','s3://','"recipe_id"','"parameters"','"feature_columns"','"model_weights"','FITTED_MODEL.bin']:
   self.assertNotIn(token,body)
  self.assertIsNone(re.search(r'\b[0-9a-f]{24}\b',body))
 def test_deterministic_page_and_pacific_date(self):
  page=self.render();self.assertEqual((ROOT/'season_review_n083.html').read_text(),page)
  self.assertIn('November 12, 2026 at 20:18:31 Pacific (PST)',page)
  self.assertIn(DATA['display_cutoff_utc'],page)
  self.assertIn('No new N083 owner result',page)
  self.assertIn('not sustained 12-core utilization',page)
 def test_completed_receipt_custody_not_remote_reread(self):
  self.assertEqual(HEALTH['new_science']['fit_entry_return_state_custody_bindings_verified'],1011)
  self.assertEqual(HEALTH['new_science']['fit_artifact_custody_bindings_verified'],3298)
  self.assertFalse(HEALTH['new_science']['individual_remote_fit_bodies_reread_by_this_publication'])

if __name__=='__main__':unittest.main()
