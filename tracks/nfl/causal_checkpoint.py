"""Credential-free admission contracts, using invented event examples in tests.

This is a small public mechanism demonstration. It does not contain the private
forecast implementation, source transforms or scientific registration.
"""
from datetime import datetime


def _clock(value):
    if not isinstance(value, str):
        raise ValueError('An explicit timestamp is required')
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('Timezone required')
    return stamp


def admit_causal_append(*, kickoff, feature_available, prediction_issued,
                        fit_completed, label_available, append_at,
                        feature_body_verified, prediction_body_verified):
    """An acquired result cannot backdate a missing pregame feature/prediction."""
    if not feature_body_verified or not prediction_body_verified:
        raise ValueError('Exact archived feature and prediction bodies required')
    start = _clock(kickoff)
    feature = _clock(feature_available)
    issue = _clock(prediction_issued)
    fit = _clock(fit_completed)
    label = _clock(label_available)
    append = _clock(append_at)
    if not (feature <= issue < start and fit <= issue):
        raise ValueError('Authenticated pregame feature, fit and issue order required')
    if not (start < label <= append):
        raise ValueError('Label must be observed after kickoff and before append')
    return {'status': 'CAUSAL_APPEND_ADMISSIBLE', 'original_issue_at': prediction_issued,
            'label_available_at': label_available, 'append_at': append_at}


def annual_checkpoint_ready(*, matrix_verified, registration_unchanged,
                            labels_causal, current_issue_completed):
    """A separately registered annual study has no current-issue dependency.

The parameter is explicit to show that current issue failure is recorded but
cannot silently alter this independent study's admission decision.
"""
    return {'annual_ready': bool(matrix_verified and registration_unchanged and labels_causal),
            'current_issue_completed': bool(current_issue_completed),
            'current_issue_required_for_annual': False}


def completion_credit(*, source_completed, source_rows, native_fit_receipts,
                      issued_forecast_receipts):
    """Only the corresponding completed receipt can award a fit or issue."""
    if any(type(x) is not int or x < 0 for x in
           [source_rows, native_fit_receipts, issued_forecast_receipts]):
        raise ValueError('Counts must be nonnegative integers')
    if source_rows and not source_completed:
        raise ValueError('An incomplete source branch cannot claim completed rows')
    return {'source_completed': bool(source_completed), 'source_rows': source_rows,
            'new_native_fits': native_fit_receipts,
            'new_forecasts': issued_forecast_receipts,
            'model_improvement_established': False}
