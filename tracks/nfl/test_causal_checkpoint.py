import unittest
from causal_checkpoint import admit_causal_append, annual_checkpoint_ready, completion_credit


class CausalCheckpointTests(unittest.TestCase):
    def base(self):
        return dict(kickoff='2030-01-06T20:00:00Z',
                    feature_available='2030-01-06T18:00:00Z',
                    prediction_issued='2030-01-06T19:00:00Z',
                    fit_completed='2030-01-05T12:00:00Z',
                    label_available='2030-01-06T23:30:00Z',
                    append_at='2030-01-07T01:00:00Z',
                    feature_body_verified=True, prediction_body_verified=True)

    def test_genuine_pregame_append_retains_issue_clock(self):
        result = admit_causal_append(**self.base())
        self.assertEqual(result['original_issue_at'], self.base()['prediction_issued'])
        self.assertNotEqual(result['append_at'], result['original_issue_at'])

    def test_new_postgame_vector_cannot_replace_archived_features(self):
        x=self.base();x['feature_available']='2030-01-06T23:40:00Z'
        with self.assertRaisesRegex(ValueError, 'pregame'):admit_causal_append(**x)

    def test_missing_predicted_body_rejects(self):
        x=self.base();x['prediction_body_verified']=False
        with self.assertRaisesRegex(ValueError, 'bodies'):admit_causal_append(**x)

    def test_fit_after_issue_rejects(self):
        x=self.base();x['fit_completed']='2030-01-06T19:01:00Z'
        with self.assertRaisesRegex(ValueError, 'order'):admit_causal_append(**x)

    def test_kickoff_issue_is_not_strictly_pregame(self):
        x=self.base();x['prediction_issued']=x['kickoff']
        with self.assertRaisesRegex(ValueError, 'pregame'):admit_causal_append(**x)

    def test_future_label_rejects(self):
        x=self.base();x['label_available']='2030-01-07T01:01:00Z'
        with self.assertRaisesRegex(ValueError, 'Label'):admit_causal_append(**x)

    def test_timezone_missing_rejects(self):
        x=self.base();x['append_at']='2030-01-07T01:00:00'
        with self.assertRaisesRegex(ValueError, 'Timezone'):admit_causal_append(**x)

    def test_independent_study_survives_current_branch_blocker(self):
        result=annual_checkpoint_ready(matrix_verified=True, registration_unchanged=True,
                                       labels_causal=True, current_issue_completed=False)
        self.assertTrue(result['annual_ready'])
        self.assertFalse(result['current_issue_required_for_annual'])

    def test_current_success_cannot_mask_changed_registration(self):
        result=annual_checkpoint_ready(matrix_verified=True, registration_unchanged=False,
                                       labels_causal=True, current_issue_completed=True)
        self.assertFalse(result['annual_ready'])

    def test_source_completion_does_not_create_model_credit(self):
        result=completion_credit(source_completed=True, source_rows=123,
                                 native_fit_receipts=0, issued_forecast_receipts=0)
        self.assertEqual(result['new_native_fits'],0)
        self.assertEqual(result['new_forecasts'],0)
        self.assertFalse(result['model_improvement_established'])

    def test_negative_and_boolean_counts_reject(self):
        for count in [-1, True]:
            with self.subTest(count=count),self.assertRaises(ValueError):
                completion_credit(source_completed=True,source_rows=count,
                                  native_fit_receipts=0,issued_forecast_receipts=0)

    def test_incomplete_source_cannot_claim_completed_rows(self):
        with self.assertRaises(ValueError):
            completion_credit(source_completed=False,source_rows=1,
                              native_fit_receipts=0,issued_forecast_receipts=0)


if __name__ == '__main__':unittest.main()
