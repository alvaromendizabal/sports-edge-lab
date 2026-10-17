"""Four tiny synthetic joint-state fits plus mathematical/contract checks."""
import copy,math,unittest
from unittest import mock
import numpy as np
import pandas as pd
from scipy.stats import multivariate_normal
from state_model import (_Filter,_config,ARMS,FIXED_CONFIG,HALF_LIFE_DAYS,fit_predict,project_scores,gaussian_crps,distribution_scores,_validate)


def fixture(track):
    rows=[]
    for i,(home,away,hp,ap) in enumerate([('A','B',24,17),('C','D',14,28),('A','C',21,21),('B','D',30,20),('A','D',27,20),('B','C',17,24),('A','B',14,31),('C','D',28,7)]):
        kickoff=pd.Timestamp('2023-09-01T18:00:00Z')+pd.Timedelta(days=7*(i//2),hours=i%2)
        rows.append(dict(track=track,game_id=track+'-'+str(i),season=2023,kickoff=kickoff,home_id=home,away_id=away,neutral=bool(i%3==0),completed=True,home_points=float(hp),away_points=float(ap),home_fbs=1,away_fbs=1))
    d=pd.DataFrame(rows);return d.iloc[:4].copy(),d.iloc[4:].iloc[[3,0,2,1]].copy()


class StateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs={};cls.progress={};cls.traces={}
        original_update=_Filter.update;original_predict=_Filter.predict
        for track in ['nfl','ncaaf']:
            train,evaluation=fixture(track)
            for arm in ARMS:
                events=[];trace=[]
                def update(state,row,release):
                    if not hasattr(state,'_test_observed'):state._test_observed=[]
                    state._test_observed.append((row.game_id,release,float(row.home_points),float(row.away_points)))
                    return original_update(state,row,release)
                def predict(state,home,away,neutral,target_release):
                    trace.append(dict(home=home,away=away,target_release=target_release,observed=list(getattr(state,'_test_observed',[]))))
                    return original_predict(state,home,away,neutral,target_release)
                with mock.patch.object(_Filter,'update',update),mock.patch.object(_Filter,'predict',predict):
                    cls.runs[(track,arm)]=fit_predict(train,evaluation,track,arm,through=2023,years=[2023],progress=lambda a,b:events.append((a,b)))
                cls.progress[(track,arm)]=events;cls.traces[(track,arm)]=trace
        cls.smoke_fits=4
    def test_exactly_four_joint_fits(self):
        self.assertEqual(self.smoke_fits,4);self.assertEqual(len(self.runs),4)
        for p,state,d in self.runs.values():self.assertEqual(d['joint_fit_attempts'],1)
    def test_output_preserves_requested_order(self):
        for (track,arm),(p,_,_) in self.runs.items():self.assertEqual(p.game_id.tolist(),fixture(track)[1].game_id.tolist())
    def test_information_clock_strictly_precedes_every_decision(self):
        for p,_,_ in self.runs.values():self.assertTrue((pd.to_datetime(p.information_upper_bound_at,utc=True)<p.decision_at).all())
    def test_observation_trace_excludes_current_and_future_results(self):
        for (track,arm),trace in self.traces.items():
            lead=FIXED_CONFIG[track]['decision_lead_hours']
            for event in trace:
                cutoff=event['target_release']-pd.Timedelta(hours=24+lead)
                self.assertTrue(all(release<cutoff for _,release,_,_ in event['observed']))
    def test_prequential_learning_declared_and_only_later_games_updated(self):
        for p,_,d in self.runs.values():
            self.assertTrue(d['prequential_evaluation_learning']);self.assertFalse(d['backward_smoothing']);self.assertEqual(d['evaluation_results_consumed'],2)
            q=p.sort_values('decision_at');self.assertEqual(q.prequential_eval_results_consumed.tolist(),[0,0,2,2])
    def test_tied_training_game_updates_joint_state(self):
        for trace in self.traces.values():
            observed=trace[0]['observed'];self.assertTrue(any(h==a==21 for _,_,h,a in observed));self.assertEqual(len(observed),4)
    def test_joint_covariance_and_exact_transformations(self):
        for p,_,_ in self.runs.values():
            self.assertTrue(((p.cov_hh*p.cov_aa-p.cov_ha**2)>0).all())
            np.testing.assert_allclose(p.margin_mean,p.home_mean-p.away_mean);np.testing.assert_allclose(p.total_mean,p.home_mean+p.away_mean)
            np.testing.assert_allclose(p.margin_var,p.cov_hh+p.cov_aa-2*p.cov_ha);np.testing.assert_allclose(p.total_var,p.cov_hh+p.cov_aa+2*p.cov_ha)
    def test_uncertainty_includes_observation_noise(self):
        for (track,_),(p,_,_) in self.runs.items():
            c=FIXED_CONFIG[track];v=c['observation_score_sd']**2;rho=c['observation_correlation']
            self.assertTrue((p.margin_var>=2*v*(1-rho)-1e-8).all());self.assertTrue((p.total_var>=2*v*(1+rho)-1e-8).all())
    def test_probabilities_and_tie_approximation(self):
        for p,_,_ in self.runs.values():
            self.assertTrue(((p.win_probability>0)&(p.win_probability<1)).all())
            np.testing.assert_allclose(p.home_win_probability_approx+p.away_win_probability_approx+p.tie_probability_approx,1.,atol=1e-14)
            np.testing.assert_allclose(p.win_probability,p.home_win_probability_approx/(1-p.tie_probability_approx),rtol=1e-12)
    def test_static_control_same_priors_and_observations(self):
        for track in ['nfl','ncaaf']:
            ps,ss,ds=self.runs[(track,'static')];pd_,sd,dd=self.runs[(track,'dynamic')]
            self.assertEqual(ds['training_updates'],dd['training_updates']);self.assertEqual(ds['evaluation_results_consumed'],dd['evaluation_results_consumed']);self.assertEqual(ss['team_games'],sd['team_games'])
            cs=copy.deepcopy(ds['config']);cd=copy.deepcopy(dd['config'])
            for c in [cs,cd]:c.pop('arm');c.pop('half_life_days')
            self.assertEqual(cs,cd);self.assertFalse(np.allclose(ps.margin_mean,pd_.margin_mean))
    def test_dynamic_half_life_and_stationary_variance(self):
        s=_Filter(_config('nfl','dynamic'));s.ensure_team('A');s.clock=pd.Timestamp('2023-01-01',tz='UTC');s.mean[2:]=[4.,-2.]
        m,p=s.moments_at(s.clock+pd.Timedelta(days=365));np.testing.assert_allclose(m[2:],[2.,-1.]);np.testing.assert_allclose(np.diag(p)[2:],[16.,16.]);self.assertEqual(HALF_LIFE_DAYS,365)
    def test_static_transition_has_zero_process_noise(self):
        s=_Filter(_config('nfl','static'));s.ensure_team('A');s.clock=pd.Timestamp('2023-01-01',tz='UTC');s.mean[2:]=[4.,-2.]
        m,p=s.moments_at(s.clock+pd.Timedelta(days=3650));np.testing.assert_array_equal(m,s.mean);np.testing.assert_array_equal(p,s.cov)
    def test_forecast_does_not_advance_filter_or_consume_labels(self):
        s=_Filter(_config('nfl','dynamic'));s.ensure_team('A');s.ensure_team('B');s.clock=pd.Timestamp('2023-01-01',tz='UTC');m=s.mean.copy();p=s.cov.copy();clock=s.clock
        a,c=s.predict('A','B',False,clock+pd.Timedelta(days=5));b,d=s.predict('A','B',False,clock+pd.Timedelta(days=5));np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(c,d);np.testing.assert_array_equal(s.mean,m);np.testing.assert_array_equal(s.cov,p);self.assertEqual(s.clock,clock)
    def test_unknown_team_forecast_preserves_persistent_state(self):
        s=_Filter(_config('nfl','dynamic'));m=s.mean.copy();c=s.cov.copy()
        s.predict('NEW_A','NEW_B',False,pd.Timestamp('2023-01-01',tz='UTC'))
        self.assertEqual(s.teams,{});self.assertEqual(s.team_games,{});self.assertIsNone(s.clock);np.testing.assert_array_equal(s.mean,m);np.testing.assert_array_equal(s.cov,c)
    def test_neutral_field_symmetric_prior(self):
        s=_Filter(_config('nfl','static'));mu,cov=s.predict('A','B',True,pd.Timestamp('2023-01-01',tz='UTC'));p=project_scores(mu,cov);self.assertEqual(p['margin_mean'],0.);self.assertAlmostEqual(p['win_probability'],.5);self.assertEqual(mu[0],mu[1])
    def test_prior_home_advantage_is_margin_not_double_margin(self):
        s=_Filter(_config('nfl','static'));mu,cov=s.predict('A','B',False,pd.Timestamp('2023-01-01',tz='UTC'));self.assertAlmostEqual(mu[0]-mu[1],2.5)
    def test_equal_training_release_rejected_before_state_fit(self):
        tr,ev=fixture('nfl');tr=tr.iloc[:1];ev=ev.iloc[:1].copy();ev['kickoff']=tr.kickoff.iloc[0]+pd.Timedelta(hours=48)
        with mock.patch('state_model._Filter',side_effect=AssertionError('State fitting must not start')):
            with self.assertRaisesRegex(ValueError,'strictly before'):fit_predict(tr,ev,'nfl','static')
    def test_fcs_input_rejected_before_state_fit(self):
        tr,ev=fixture('ncaaf');tr.loc[tr.index[0],'away_fbs']=0
        with mock.patch('state_model._Filter',side_effect=AssertionError('State fitting must not start')):
            with self.assertRaisesRegex(ValueError,'FBS-v-FBS'):fit_predict(tr,ev,'ncaaf','dynamic')
    def test_malformed_scores_rejected(self):
        tr,_=fixture('nfl');tr.loc[0,'home_points']=np.nan
        with self.assertRaisesRegex(ValueError,'scores'):_validate(tr,'nfl',True)
    def test_backward_clock_rejected(self):
        s=_Filter(_config('nfl','dynamic'));s.clock=pd.Timestamp('2023-01-02',tz='UTC')
        with self.assertRaisesRegex(ValueError,'backward'):s.moments_at(pd.Timestamp('2023-01-01',tz='UTC'))
    def test_gaussian_crps_known_standard_normal_value(self):
        expected=(math.sqrt(2)-1)/math.sqrt(math.pi);self.assertAlmostEqual(gaussian_crps([0.],[0.],[1.])[0],expected,places=12)
    def test_joint_nll_matches_scipy(self):
        p=pd.DataFrame([project_scores([20.,24.],[[100.,10.],[10.,100.]])]);r=distribution_scores([21.],[25.],p)
        expected=-multivariate_normal.logpdf([21.,25.],mean=[20.,24.],cov=[[100.,10.],[10.,100.]])
        self.assertAlmostEqual(r['joint_gaussian_nll'],expected,places=12)
    def test_interval_width_and_coverage_at_predictive_mean(self):
        p=pd.DataFrame([project_scores([20.,24.],[[100.,10.],[10.,100.]])]);r=distribution_scores([20.],[24.],p)
        for task in ['margin','total']:
            intervals=r[task]['intervals'];self.assertTrue(all(x['empirical_coverage']==1 for x in intervals));self.assertGreater(intervals[1]['mean_width'],intervals[0]['mean_width'])
            self.assertGreater(r[task]['gaussian_crps'],0)
    def test_incoherent_moments_rejected(self):
        p=pd.DataFrame([project_scores([20.,24.],[[100.,10.],[10.,100.]])]);p['margin_var']=1.
        with self.assertRaisesRegex(ValueError,'Incoherent'):distribution_scores([20.],[24.],p)
    def test_unknown_publication_retained_null(self):
        for p,s,d in self.runs.values():self.assertTrue(p.source_publication_at.isna().all());self.assertIsNone(s['source_publication_at']);self.assertIsNone(d['source_publication_at']);self.assertFalse(d['strict_point_in_time_verified'])
    def test_progress_start_and_completion(self):
        for events in self.progress.values():self.assertEqual(events[0],(0,8));self.assertEqual(events[-1],(8,8))
    def test_final_state_covariance_psd(self):
        for _,s,_ in self.runs.values():self.assertGreaterEqual(np.linalg.eigvalsh(np.asarray(s['covariance'])).min(),-1e-9)


if __name__=='__main__':unittest.main(verbosity=2)
