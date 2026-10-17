"""Reporting-only tests: no fitting, feature changes or selection changes."""
import unittest
import numpy as np
import pandas as pd
from common import GateError
from metrics import brier_skill
from experiments import reporting_labels,attach_reporting,diagnostic_slices,REPORT_LEVELS,compare,market_compare,columns


class ReportingTests(unittest.TestCase):
    def frame(self,track='nfl'):
        f=pd.DataFrame(dict(track=[track]*6,game_id=['fixture-'+str(i) for i in range(6)],season=[2024]*6,week=list(range(1,7)),kickoff=pd.date_range('2024-09-01',periods=6,freq='7D',tz='UTC'),neutral=[1,0,np.nan,0,1,0],home_fbs=[1,1,0,0,np.nan,1],away_fbs=[1,0,1,0,1,1],home_games=[0,3,0,3,np.nan,3],away_games=[0,0,3,3,2,3],qb_home_has_prior_qb=[1,1,0,np.nan,0,1],qb_away_has_prior_qb=[1,0,0,1,1,1],eff_home_missing=[0,0,1,np.nan,1,0],eff_away_missing=[0,1,1,0,0,0],target=[0.,1.,0.,1.,0.,1.],accepted=[.5]*6,same_features_linear=[.5]*6,hgb=[.2,.8,.2,.8,.2,.8],mlp=[.3,.7,.3,.7,.3,.7]))
        f['decision_at']=f.kickoff-pd.Timedelta(hours=24);f['information_upper_bound_at']=f.decision_at
        return f
    def test_known_brier_skill_formula(self):
        r=brier_skill([0,1],[.2,.8],[.5,.5]);self.assertAlmostEqual(r['value'],.84);self.assertEqual(r['n'],2);self.assertIsNone(r['reason']);self.assertTrue(r['same_cohort'])
    def test_zero_reference_is_undefined_with_reason(self):
        r=brier_skill([0,1],[.2,.8],[0,1]);self.assertIsNone(r['value']);self.assertEqual(r['reference_brier'],0);self.assertEqual(r['reason'],'zero_reference_brier')
    def test_mismatched_skill_arrays_rejected(self):
        with self.assertRaises(GateError):brier_skill([0,1],[.2],[.5,.5])
    def test_skill_probability_bounds_rejected(self):
        with self.assertRaises(GateError):brier_skill([0,1],[-.1,.8],[.5,.5])
    def test_nfl_partitions_exhaustive_and_mutually_exclusive(self):
        f=self.frame();labels=reporting_labels(f,'nfl')
        for d,levels in REPORT_LEVELS.items():
            memberships=np.column_stack([(labels[d]==v).to_numpy() for v in levels]);np.testing.assert_array_equal(memberships.sum(axis=1),np.ones(len(f)))
        self.assertEqual(set(labels.matchup),{'not_applicable'});self.assertEqual(labels.venue.tolist(),['neutral','home_venue','unknown','home_venue','neutral','home_venue'])
    def test_college_partitions_exhaustive_and_unknown_retained(self):
        f=self.frame('ncaaf');labels=reporting_labels(f,'ncaaf')
        for d,levels in REPORT_LEVELS.items():
            self.assertEqual(sum(int((labels[d]==v).sum()) for v in levels),len(f));self.assertTrue(labels[d].notna().all())
        self.assertEqual(labels.matchup.tolist(),['fbs_vs_fbs','fbs_vs_fcs','fbs_vs_fcs','neither_fbs','unknown','fbs_vs_fbs'])
        self.assertEqual(labels.information_coverage.tolist(),['both_available','one_available','neither_available','unknown','one_available','both_available'])
    def test_metadata_does_not_mutate_rows_or_feature_list(self):
        f=self.frame();original=f.copy(deep=True);before={t:columns(t) for t in ['nfl','ncaaf']};out=attach_reporting(f,'nfl');pd.testing.assert_frame_equal(f,original);pd.testing.assert_frame_equal(out[f.columns],original)
        self.assertEqual(before,{t:columns(t) for t in before});self.assertTrue(all(not c.startswith('report_') for t in before for c in columns(t)))
    def test_small_and_empty_slices_report_counts_without_ci_or_promotion(self):
        d=diagnostic_slices(self.frame(),'nfl','win');self.assertFalse(d['subgroup_promotion'])
        for dimension in REPORT_LEVELS:self.assertEqual(sum(x['n'] for x in d['rows'] if x['dimension']==dimension),6)
        for row in d['rows']:
            self.assertFalse(row['subgroup_promotion']);self.assertIn(row['support'],['empty','insufficient_rows'])
            for refs in row['paired_uncertainty'].values():
                for ci in refs.values():self.assertIsNone(ci['lower95']);self.assertIsNone(ci['upper95']);self.assertEqual(ci['blocks'],row['season_week_blocks'])
    def test_fewer_than_eight_blocks_has_no_interval(self):
        f=pd.concat([self.frame()]*6,ignore_index=True);d=diagnostic_slices(f,'nfl','win');row=next(r for r in d['rows'] if r['dimension']=='matchup' and r['label']=='not_applicable')
        self.assertEqual(row['n'],36);self.assertEqual(row['support'],'insufficient_blocks');self.assertIsNone(row['paired_uncertainty']['hgb']['accepted']['upper95'])
    def test_cached_reference_skill_is_same_cohort(self):
        f=self.frame();r=compare(f,'nfl','win');self.assertAlmostEqual(r['candidates']['hgb']['brier_skill_vs_references']['accepted']['value'],.84);self.assertAlmostEqual(r['candidates']['mlp']['brier_skill_vs_references']['same_features_linear']['value'],.64)
    def test_market_skill_uses_only_matched_rows(self):
        f=self.frame();f.loc[2:,'hgb']=.99
        m=f.iloc[:2][['track','game_id','season','kickoff','target']].copy();m['task']='win';m['model_prediction']=.5;m['market_prediction']=.5;m['snapshot_at']=m.kickoff-pd.Timedelta(hours=1)
        r=market_compare(f,'nfl','win',m);self.assertEqual(r['n'],2);self.assertEqual(r['brier_skill_vs_market']['hgb']['n'],2);self.assertAlmostEqual(r['brier_skill_vs_market']['hgb']['value'],.84)
    def test_missing_reporting_metadata_fails_closed(self):
        with self.assertRaisesRegex(GateError,'reporting metadata'):reporting_labels(self.frame().drop(columns='neutral'),'nfl')


if __name__=='__main__':unittest.main(verbosity=2)
