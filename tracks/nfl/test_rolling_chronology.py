import copy
import unittest
from rolling_chronology import (admitted_training_labels, classify_forecast, clock, digest,
                                invented_inputs, matured_feedback, weekly_origin)


class RollingChronologyTests(unittest.TestCase):
    def setUp(self):
        self.policy, self.games, self.labels, self.feedback = invented_inputs()
        self.origin = weekly_origin(self.policy, self.games)

    def result(self):
        return matured_feedback(self.policy, self.origin, 'winner', self.feedback)

    def forecast(self):
        return dict(policy_id=self.policy['policy_id'], kickoff='2031-09-14T17:00:00Z',
                    model_completed_at='2031-09-14T14:45:00Z', latest_input_available_at='2031-09-14T14:59:00Z',
                    created_at='2031-09-14T15:00:00Z', issued_at='2031-09-14T15:00:00Z', observed_at='2031-09-14T16:00:00Z')

    def test_week_origin_uses_earliest_kickoff_not_iso_week(self):
        self.games.append(dict(self.games[0], game_id='invented-thursday', kickoff='2031-09-11T23:00:00Z'))
        self.assertEqual(weekly_origin(self.policy, self.games)['fit_information_before'], '2031-09-11T21:00:00+00:00')

    def test_week_order_is_irrelevant(self):
        self.games.append(dict(self.games[0], game_id='invented-second', kickoff='2031-09-14T20:00:00Z'))
        a=weekly_origin(self.policy,self.games); self.games.reverse()
        self.assertEqual(a,weekly_origin(self.policy,self.games))

    def test_duplicate_game_rejected(self):
        with self.assertRaises(ValueError): weekly_origin(self.policy,self.games*2)

    def test_mixed_official_week_rejected(self):
        with self.assertRaises(ValueError): weekly_origin(self.policy,self.games+[dict(self.games[0],game_id='other',week=3)])

    def test_naive_clock_rejected_and_equivalent_timezone_equal(self):
        with self.assertRaises(ValueError): clock('2031-09-14T15:00:00')
        self.assertEqual(clock('2031-09-14T15:00:00Z'),clock('2031-09-14T08:00:00-07:00'))

    def test_reconstruction_origin_is_explicit(self):
        self.policy['registered_at']='2031-10-01T00:00:00Z'
        self.assertTrue(weekly_origin(self.policy,self.games)['historical_reconstruction'])

    def test_current_labels_need_separate_rolling_policy(self):
        self.assertEqual(admitted_training_labels(self.policy,self.origin,self.labels)['admitted_game_ids'],['invented-week1'])
        self.policy.update(mode='FROZEN_HISTORICAL',policy_id='invented-frozen')
        self.origin=weekly_origin(self.policy,self.games)
        r=admitted_training_labels(self.policy,self.origin,self.labels)
        self.assertEqual(r['admitted_game_ids'],[])
        self.assertEqual(r['excluded'][0]['reason'],'CURRENT_LABEL_EXCLUDED_BY_FROZEN_POLICY')

    def test_same_target_event_never_trains_itself(self):
        self.labels[0]['game_id']=self.games[0]['game_id']
        r=admitted_training_labels(self.policy,self.origin,self.labels)
        self.assertEqual(r['excluded'][0]['reason'],'EVALUATION_EVENT_IS_NOT_A_TRAINING_LABEL')

    def test_label_boundary_strict_and_missing_unknown(self):
        for value in ('2031-09-14T15:00:00Z','2031-09-14T15:00:01Z',None):
            with self.subTest(value=value):
                self.labels[0]['available_at']=value
                self.assertFalse(admitted_training_labels(self.policy,self.origin,self.labels)['admitted_game_ids'])

    def test_duplicate_labels_rejected(self):
        with self.assertRaises(ValueError): admitted_training_labels(self.policy,self.origin,self.labels*2)

    def test_changed_policy_cannot_reuse_origin(self):
        self.policy['horizon_hours']=1
        with self.assertRaises(ValueError): admitted_training_labels(self.policy,self.origin,self.labels)
        with self.assertRaises(ValueError): self.result()

    def test_monitored_selection_and_promotion_forbidden(self):
        for field in ('selection_uses_monitored_outcomes','promotion_permitted'):
            with self.subTest(field=field):
                p=copy.deepcopy(self.policy);p[field]=True
                with self.assertRaises(ValueError):weekly_origin(p,self.games)

    def test_origin_event_membership_cannot_silently_change(self):
        self.origin['game_ids']=['replacement']
        with self.assertRaises(ValueError):admitted_training_labels(self.policy,self.origin,self.labels)
        with self.assertRaises(ValueError):self.result()

    def test_origin_policy_name_is_bound_for_feedback_too(self):
        self.origin['policy_id']='different-policy'
        with self.assertRaises(ValueError):self.result()

    def test_matured_oof_feedback_arithmetic(self):
        row=self.result()['rows'][0]
        self.assertAlmostEqual(row['model_residual'],.3)
        self.assertAlmostEqual(row['reference_residual'],.4)
        self.assertAlmostEqual(row['signed_disagreement'],.1)

    def test_future_outcome_mutation_does_not_affect_current_feedback(self):
        baseline=self.result()
        future=dict(self.feedback[0],game_id='future',outcome_available_at='2031-09-15T00:00:00Z',actual=0)
        self.feedback.append(future);a=self.result();self.feedback[-1]['actual']=1;b=self.result()
        self.assertEqual(a,b);self.assertEqual(a['rows'],baseline['rows'])

    def test_in_sample_prediction_is_not_feedback(self):
        self.feedback[0]['training_game_ids'].append(self.feedback[0]['game_id'])
        self.assertEqual(self.result()['excluded'][0]['reason'],'NOT_FORWARD_OUT_OF_FOLD')

    def test_unresolved_outcome_not_zero_residual(self):
        self.feedback[0]['outcome_available_at']=None
        self.assertEqual(self.result()['rows'],[])
        self.assertEqual(self.result()['excluded'][0]['reason'],'UNRESOLVED_OUTCOME_CLOCK')

    def test_current_week_never_in_meta_training(self):
        self.feedback[0]['game_id']=self.games[0]['game_id']
        self.assertEqual(self.result()['excluded'][0]['reason'],'CURRENT_WEEK_FEEDBACK_FORBIDDEN')

    def test_other_target_is_reported_exclusion(self):
        self.feedback[0]['target']='total'
        self.assertEqual(self.result()['excluded'][0]['reason'],'DIFFERENT_TARGET')

    def test_duplicate_feedback_rejected(self):
        self.feedback*=2
        with self.assertRaises(ValueError):self.result()

    def test_late_prior_fit_and_feature_are_rejected(self):
        for field in ('latest_training_label_at','latest_feature_available_at'):
            with self.subTest(field=field):
                old=self.feedback[0][field];self.feedback[0][field]=self.feedback[0]['prior_information_before']
                self.assertFalse(self.result()['rows']);self.feedback[0][field]=old

    def test_later_prior_horizon_not_silently_converted(self):
        self.feedback[0]['prior_information_before']='2031-09-07T16:00:00Z'
        self.assertEqual(self.result()['excluded'][0]['reason'],'PRIOR_HORIZON_TOO_LATE')

    def test_outcome_before_game_rejected(self):
        self.feedback[0]['outcome_available_at']='2031-09-06T00:00:00Z'
        with self.assertRaises(ValueError):self.result()

    def test_unknown_probability_and_tie_not_binary_loss(self):
        for value in (None,float('nan'),True,.5):
            with self.subTest(value=value):
                self.feedback[0]['actual']=value
                with self.assertRaises(ValueError):self.result()

    def test_points_allow_real_values_without_probability_claim(self):
        self.feedback[0].update(target='margin',actual=7,prediction=4,reference=3)
        r=matured_feedback(self.policy,self.origin,'margin',self.feedback)
        self.assertEqual(r['rows'][0]['model_residual'],3)
        self.assertNotIn('cover_probability',r)

    def test_timely_forecast_requires_separate_durable_proof(self):
        self.assertEqual(classify_forecast(self.policy,self.forecast()),'DECLARED_TIMELY_PREGAME_REQUIRES_DURABLE_ISSUE_PROOF')

    def test_backdated_creation_or_future_issue_rejected(self):
        for changes in ({'created_at':'2031-09-14T16:01:00Z'},{'issued_at':'2031-09-14T16:01:00Z'},
                        {'model_completed_at':'2031-09-14T15:01:00Z'}, {'latest_input_available_at':'2031-09-14T15:01:00Z'}):
            with self.subTest(changes=changes):
                r=self.forecast();r.update(changes)
                with self.assertRaises(ValueError):classify_forecast(self.policy,r)

    def test_late_pregame_is_not_timely(self):
        r=self.forecast();r.update(created_at='2031-09-14T15:01:00Z',issued_at='2031-09-14T15:01:00Z')
        self.assertEqual(classify_forecast(self.policy,r),'LATE_PREGAME_MONITORING')

    def test_started_game_prediction_is_reconstruction(self):
        r=self.forecast();r.update(created_at='2031-09-14T17:00:00Z',issued_at='2031-09-14T17:00:00Z',observed_at='2031-09-14T18:00:00Z')
        self.assertEqual(classify_forecast(self.policy,r),'RECONSTRUCTED_AFTER_EVENT_START')

    def test_exact_cutoff_input_is_excluded_under_strict_policy(self):
        r=self.forecast();r['latest_input_available_at']=r['created_at']
        self.assertEqual(classify_forecast(self.policy,r),'INPUT_OUTSIDE_STRICT_REGISTERED_HORIZON')

    def test_registration_cannot_be_backdated(self):
        self.policy['registered_at']='2031-09-15T00:00:00Z'
        self.assertEqual(classify_forecast(self.policy,self.forecast()),'RECONSTRUCTION_BEFORE_POLICY_REGISTRATION')

    def test_no_input_mutation_fit_promotion_or_original_issue_claim(self):
        before=copy.deepcopy((self.policy,self.origin,self.feedback));r=self.result()
        self.assertEqual(before,(self.policy,self.origin,self.feedback))
        self.assertEqual(r['new_fits'],0);self.assertFalse(r['promotion_permitted'])
        self.assertIn('NO_ORIGINAL_ISSUE_CLAIM',r['rows'][0]['evidence_class'])


if __name__=='__main__':unittest.main()
