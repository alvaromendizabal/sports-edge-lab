"""Separate market display clocks from causal forecast evaluation.

No source acquisition, model fitting or quote interpolation happens here. A
recorded historical quote may be fetched later. Its genuine event timestamp,
not that later fetch time, determines which pregame reference it can support.
"""
from datetime import datetime, timedelta

HORIZON_LABELS = {
    "T2": "2 hours before kickoff",
    "T1": "1 hour before kickoff",
    "LATEST_PREGAME": "Latest before kickoff",
    "LATEST_OBSERVED": "Latest observed upcoming",
}


def instant(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Evidence clocks must include a timezone")
    return result


def reference_clock(*, kickoff, quote_at, acquired_at, horizon):
    """Validate a genuine observed reference; never imply execution eligibility.

    A quote need not occur exactly on the cutoff minute. It must be the
    authenticated last available observation chosen by the source adapter.
    This public contract checks time admissibility, not source completeness.
    """
    if horizon not in HORIZON_LABELS:
        raise ValueError("Unknown market reference horizon")
    kick, quote, acquired = map(instant, (kickoff, quote_at, acquired_at))
    if quote > acquired:
        raise ValueError("Quote timestamp is after its acquisition")
    cutoff = kick - timedelta(hours={"T2": 2, "T1": 1}.get(horizon, 0))
    if horizon in ("T2", "T1") and quote > cutoff:
        raise ValueError("Quote is later than the named cutoff")
    if horizon == "LATEST_PREGAME" and quote >= kick:
        raise ValueError("Pregame reference must precede kickoff")
    if horizon == "LATEST_OBSERVED" and (quote >= kick or acquired >= kick):
        raise ValueError("Upcoming observation cannot be an in-game snapshot")
    return {
        "horizon": horizon,
        "label": HORIZON_LABELS[horizon],
        "quote_age_at_cutoff_seconds": (cutoff - quote).total_seconds(),
        "acquired_after_kickoff": acquired >= kick,
        "execution_qualified": False,
    }


def comparison_role(*, model_horizon, quote_horizon, issue_class):
    """Later market benchmarks are publishable without backdating the model."""
    if quote_horizon not in HORIZON_LABELS:
        raise ValueError("Unknown market reference horizon")
    issue_classes = {"RECONSTRUCTED_NOT_ORIGINAL_ISSUED", "UNAVAILABLE",
                     "EARLY_FORWARD_RESEARCH_ISSUE", "T1_RESEARCH_ACTUAL_ISSUE"}
    if issue_class not in issue_classes:
        raise ValueError("Unknown forecast issue class")
    original = issue_class in ("EARLY_FORWARD_RESEARCH_ISSUE", "T1_RESEARCH_ACTUAL_ISSUE")
    same_cutoff = model_horizon == quote_horizon and quote_horizon in ("T1", "T2")
    return {
        "same_cutoff": same_cutoff,
        "original_issue": original,
        "role": ("Same-cutoff reconstruction" if same_cutoff and not original
                 else "Same-cutoff issued forecast" if same_cutoff
                 else "Separate market reference; information times differ"),
        "execution_qualified": False,
    }
