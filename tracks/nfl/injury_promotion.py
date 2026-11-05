"""Credential-free, invented promotion contract; not the private NFL selector.

Collection, point-in-time eligibility, research selection and promotion are
separate states. This demo implements explicit admission checks, not a model or
an injury-adjustment heuristic. Run: python tracks/nfl/injury_promotion.py --demo
"""
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import argparse
import json
import math


def _instant(value):
    if not isinstance(value, str):
        raise ValueError('A clock must be a timezone-aware ISO string')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('Invalid clock') from exc
    if parsed.tzinfo is None:
        raise ValueError('Naive clocks are not admissible')
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class Source:
    observed_at: str
    published_at: str | None
    report_season: int | None
    game_season: int
    player_identity_verified: bool
    content_replayed: bool
    current_roster_only: bool = False


def source_status(source, cutoff, *, historical):
    """Return evidence states; never infer missing reports to mean healthy."""
    cut = _instant(cutoff)
    observed = _instant(source.observed_at)
    if not source.content_replayed or not source.player_identity_verified:
        return 'IDENTITY_OR_SOURCE_UNVERIFIED'
    if source.current_roster_only:
        return 'CONTEXT_ONLY_ROSTER_IS_NOT_INJURY_STATUS'
    if source.report_season != source.game_season:
        return 'REPORT_VINTAGE_UNVERIFIED'
    if historical:
        if source.published_at is None:
            return 'HISTORICAL_AVAILABILITY_UNVERIFIED'
        available = _instant(source.published_at)
        if available > observed:
            return 'PUBLICATION_AFTER_OBSERVATION_CONFLICT'
    else:
        available = observed
    return 'ELIGIBLE_AT_CUTOFF' if available <= cut else 'AFTER_CUTOFF'


@dataclass(frozen=True)
class Experiment:
    target: str
    baseline_events: tuple[str, ...]
    candidate_events: tuple[str, ...]
    selection_label_times: tuple[str, ...]
    selection_boundary: str
    frozen_before_evaluation: bool
    native_models_authenticated: bool
    max_fold_training_label_at: str
    fold_prediction_at: str
    paired_improvement_interval: tuple[float, float] | None
    current_input_coverage_verified: bool
    registered_acceptance_passed: bool


def promotion_status(experiment):
    """All flags are evidence obligations, never values inferred from accuracy.

The interval expresses candidate loss minus baseline loss, so a wholly
negative interval supports lower candidate loss on the registered common cohort.
This invented rule is illustrative; it does not authorize real NFL promotion.
"""
    e = experiment
    if e.target not in {'winner', 'margin', 'total'}:
        raise ValueError('Unknown target')
    if (not e.baseline_events or len(set(e.baseline_events)) != len(e.baseline_events)
            or len(set(e.candidate_events)) != len(e.candidate_events)
            or set(e.baseline_events) != set(e.candidate_events)):
        return 'BLOCKED_UNMATCHED_OR_DUPLICATE_EVENTS'
    boundary = _instant(e.selection_boundary)
    if not e.selection_label_times or any(_instant(t) >= boundary for t in e.selection_label_times):
        return 'BLOCKED_SELECTION_LABEL_AVAILABILITY'
    if _instant(e.max_fold_training_label_at) >= _instant(e.fold_prediction_at):
        return 'BLOCKED_FOLD_LABEL_LEAKAGE'
    if not e.frozen_before_evaluation or not e.native_models_authenticated:
        return 'BLOCKED_RECIPE_OR_MODEL_IDENTITY'
    interval = e.paired_improvement_interval
    if interval is None or len(interval) != 2:
        return 'RESEARCH_ONLY_UNCERTAINTY_UNAVAILABLE'
    lo, hi = interval
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in interval) or lo > hi:
        raise ValueError('Invalid paired interval')
    if hi >= 0:
        return 'RESEARCH_ONLY_IMPROVEMENT_NOT_ESTABLISHED'
    if not e.current_input_coverage_verified:
        return 'RESEARCH_ONLY_CURRENT_INPUTS_INCOMPLETE'
    if not e.registered_acceptance_passed:
        return 'RESEARCH_ONLY_ACCEPTANCE_PENDING'
    return 'DEMO_PROMOTION_ELIGIBLE_NOT_A_REAL_MODEL_DECISION'


def demo():
    source = Source('2023-09-10T15:00:00Z', '2023-09-10T14:00:00Z', 2023, 2023, True, True)
    trial = Experiment('winner', ('invented-a', 'invented-b'), ('invented-b', 'invented-a'),
                       ('2022-12-01T12:00:00Z',), '2024-01-01T00:00:00Z', True, True,
                       '2022-12-01T12:00:00Z', '2023-09-10T16:00:00Z', (-.04, .01), False, False)
    return {'data': 'INVENTED_FIXTURES_ONLY',
            'source_at_cutoff': source_status(source, '2023-09-10T16:00:00Z', historical=True),
            'downloaded_later_same_publication': source_status(replace(source, observed_at='2026-01-01T00:00:00Z'), '2023-09-10T16:00:00Z', historical=True),
            'unverifiable_archive': source_status(replace(source, published_at=None), '2023-09-10T16:00:00Z', historical=True),
            'strong_point_estimate_uncertain': promotion_status(trial),
            'better_interval_incomplete_inputs': promotion_status(replace(trial, paired_improvement_interval=(-.04, -.01))),
            'no_owner_research_or_promotion_performed': True}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', required=True)
    parser.parse_args()
    print(json.dumps(demo(), indent=2))
