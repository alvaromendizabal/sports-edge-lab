"""Synthetic and mathematical-only situation representation checks; no model fits."""
import unittest
import numpy as np
import pandas as pd
from fixtures import synthetic_games, synthetic_raw
from data import build_features as baseline_features
from nfl_situation import aggregate_pbp, build_features, feature_columns, METRICS, FALLBACK, RAW_COLUMNS

class SituationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.games=synthetic_games(); cls.games=cls.games[(cls.games.season==2016)&(cls.games.week<=4)].copy().reset_index(drop=True)
  cls.frame=baseline_features(cls.games);cls.raw=synthetic_raw(cls.games)
  cls.panel,cls.audit,cls.bad=aggregate_pbp(cls.raw,cls.frame)
  cls.aug,cls.built,cls.prov=build_features(cls.frame,cls.panel)
 def test_width_finite_and_upstream_preserved(self):
  self.assertEqual(len(feature_columns()),52);self.assertTrue(np.isfinite(self.aug[feature_columns()].to_numpy()).all())
  pd.testing.assert_frame_equal(self.aug[self.frame.columns],self.frame)
 def test_unique_team_game_and_release(self):
  self.assertEqual(len(self.panel),2*len(self.games));self.assertFalse(self.panel.duplicated(['game_id','team_id']).any())
  self.assertTrue((self.panel.available_at==self.panel.kickoff+pd.Timedelta(hours=24)).all())
 def test_exact_duplicate_reused(self):
  panel,a,b=aggregate_pbp(pd.concat([self.raw,self.raw.iloc[[0]]]),self.frame)
  pd.testing.assert_frame_equal(panel,self.panel);self.assertEqual(a['counts']['identical_duplicates_removed'],1)
 def test_conflict_quarantines_whole_game(self):
  q=self.raw.iloc[[0]].copy();q['yards_gained']=98
  p,a,b=aggregate_pbp(pd.concat([self.raw,q]),self.frame)
  self.assertNotIn(q.iloc[0].game_id,set(p.game_id));self.assertTrue(b.reason.str.contains('conflicting').all())
 def test_bad_team_and_nonfinite_quarantined(self):
  raw=self.raw.copy();raw.loc[0,'posteam']='XXX';raw.loc[1,'yards_gained']=np.inf
  p,a,b=aggregate_pbp(raw,self.frame);self.assertEqual(len(b),2)
 def test_noncanonical_excluded(self):
  q=self.raw.iloc[[0]].copy();q['game_id']='2099_01_BUF_ARI'
  p,a,b=aggregate_pbp(pd.concat([self.raw,q]),self.frame);pd.testing.assert_frame_equal(p,self.panel)
 def test_canonical_identity_fails_closed(self):
  f=self.frame.copy();f.loc[0,'home_id']='NE'
  with self.assertRaises(Exception):aggregate_pbp(self.raw,f)
 def test_flags_and_admin_exclusions(self):
  raw=self.raw.copy();raw.loc[0,'qb_dropback']=3;raw.loc[1,'penalty']=1
  p,a,b=aggregate_pbp(raw,self.frame);self.assertEqual(len(b),1);self.assertEqual(int(p.neutral_plays.sum()),len(raw)-2)
 def test_neutral_boundaries(self):
  raw=self.raw.copy();raw.loc[0,'qtr']=4;raw.loc[1,'score_differential']=9;raw.loc[2,'half_seconds_remaining']=120
  p,a,b=aggregate_pbp(raw,self.frame);self.assertEqual(int(p.neutral_plays.sum()),len(raw)-3)
 def test_non_early_down_kept_only_neutral(self):
  raw=self.raw.copy();raw.loc[0,'down']=3
  p,a,b=aggregate_pbp(raw,self.frame);self.assertEqual(int(p.neutral_plays.sum()),len(raw));self.assertEqual(int(p.ed_dropbacks.sum()+p.ed_runs.sum()),len(raw)-1)
 def test_current_and_future_outcomes_cannot_affect_first(self):
  raw=self.raw.copy();raw['yards_gained']=97
  p,_,_=aggregate_pbp(raw,self.frame);f,_,_=build_features(self.frame,p)
  first=self.frame.kickoff==self.frame.kickoff.min()
  np.testing.assert_array_equal(f.loc[first,feature_columns()],self.aug.loc[first,feature_columns()])
 def test_non_cold_target_and_future_play_mutations_do_not_change_target(self):
  target=self.frame[self.frame.week==3].sort_values('kickoff').iloc[0]
  future=set(self.frame.loc[self.frame.kickoff>=target.kickoff,'game_id'])
  raw=self.raw.copy();raw.loc[raw.game_id.isin(future),'yards_gained']=97
  p,_,_=aggregate_pbp(raw,self.frame);f,_,_=build_features(self.frame,p)
  mask=f.game_id==target.game_id
  np.testing.assert_array_equal(f.loc[mask,feature_columns()],self.aug.loc[mask,feature_columns()])
 def test_first_release_batch_shrinkage_and_no_simultaneous_opponent_update(self):
  f=self.frame.copy();first=f.week==1;f.loc[first,'kickoff']=f.loc[first,'kickoff'].min()
  # Mutate another first-release game. Its effect on the league prior is allowed,
  # but all first-game opponent corrections must still be exactly zero.
  raw=self.raw.copy();changed=f[first].sort_values('game_id').iloc[0].game_id
  raw.loc[raw.game_id==changed,'yards_gained']=30
  p,_,_=aggregate_pbp(raw,f);a,_,_=build_features(f,p)
  first_panel=p[p.game_id.isin(f.loc[first,'game_id'])]
  for target in f[f.week==2].itertuples():
   row=a[a.game_id==target.game_id].iloc[0]
   for side,team in [('home',target.home_id),('away',target.away_id)]:
    own=first_panel[first_panel.team_id==team].iloc[0]
    for m in METRICS:
     league=first_panel[m+'_sum'].sum()/first_panel[m+'_n'].sum()
     expected=(own[m+'_sum']+100*league)/(own[m+'_n']+100)
     self.assertAlmostEqual(row['sit_'+side+'_off_'+m],expected,places=12)
 def test_last_eight_game_cap(self):
  g=synthetic_games();g=g[g.season==2016];f=baseline_features(g)
  p,_,_=aggregate_pbp(synthetic_raw(g),f);a,_,_=build_features(f,p)
  self.assertEqual(a.sit_home_prior_games_scaled.max(),1)
  self.assertEqual(a.sit_away_prior_games_scaled.max(),1)
  self.assertTrue((a.loc[a.week==12,'sit_home_prior_games_scaled']==1).all())
 def test_cold_start_fixed_fallbacks(self):
  r=self.aug.loc[self.aug.kickoff.idxmin()]
  for side in ['home','away']:
   for role in ['off','allowed']:
    for metric,v in FALLBACK.items():self.assertEqual(r[f'sit_{side}_{role}_{metric}'],v)
 def test_strict_availability_boundary(self):
  f=self.frame.copy();g=f.sort_values('kickoff').iloc[0];target=f[f.game_id!=g.game_id].sort_values('kickoff').iloc[0]
  f.loc[f.game_id==target.game_id,'kickoff']=g.kickoff+pd.Timedelta(hours=48)
  p,_,_=aggregate_pbp(self.raw,f);a,_,_=build_features(f,p)
  row=a[a.game_id==target.game_id].iloc[0];self.assertTrue(pd.isna(row.situation_max_available_at))
  f.loc[f.game_id==target.game_id,'kickoff']+=pd.Timedelta(nanoseconds=1)
  p,_,_=aggregate_pbp(self.raw,f);a,_,_=build_features(f,p)
  row=a[a.game_id==target.game_id].iloc[0];self.assertEqual(row.situation_max_available_at,g.kickoff+pd.Timedelta(hours=24))
 def test_same_release_row_order_invariant(self):
  f=self.frame.copy();week=f.week==1;f.loc[week,'kickoff']=f.loc[week,'kickoff'].min()
  p,_,_=aggregate_pbp(self.raw,f);a,_,_=build_features(f,p)
  q,_,_=aggregate_pbp(self.raw.sample(frac=1,random_state=1),f);b,_,_=build_features(f,q.sample(frac=1,random_state=2))
  np.testing.assert_allclose(a[feature_columns()],b[feature_columns()])
 def test_history_expiry(self):
  f=self.frame.copy();last=f.kickoff.idxmax();f.loc[last,'kickoff']=f.kickoff.max()+pd.Timedelta(days=370)
  p,_,_=aggregate_pbp(self.raw,f);a,_,_=build_features(f,p)
  self.assertEqual(a.loc[last,'sit_home_prior_games_scaled'],0);self.assertEqual(a.loc[last,'sit_away_prior_games_scaled'],0)
 def test_missing_game_has_no_invented_source(self):
  gid=self.games.iloc[0].game_id;p=self.panel[self.panel.game_id!=gid]
  a,audit,prov=build_features(self.frame,p);self.assertTrue(np.isfinite(a[feature_columns()].to_numpy()).all());self.assertGreaterEqual(audit['missing_released_games'],1)
 def test_temporal_metadata(self):
  self.assertTrue((self.aug.situation_max_available_at.dropna()<self.aug.loc[self.aug.situation_max_available_at.notna(),'situation_decision_at']).all())
  self.assertTrue(self.prov.source_publication_at.isna().all());self.assertFalse(self.prov.strict_point_in_time_verified.any())
 def test_tampered_release_fails(self):
  p=self.panel.copy();p.loc[0,'available_at']+=pd.Timedelta(hours=1)
  with self.assertRaises(Exception):build_features(self.frame,p)
 def test_tampered_denominator_fails(self):
  p=self.panel.copy();p.loc[0,'ed_dropback_ypp_n']=-1
  with self.assertRaises(Exception):build_features(self.frame,p)
 def test_partial_input_schema_fails(self):
  with self.assertRaises(Exception):aggregate_pbp(self.raw.drop(columns=[RAW_COLUMNS[-1]]),self.frame)

if __name__=='__main__':unittest.main()
