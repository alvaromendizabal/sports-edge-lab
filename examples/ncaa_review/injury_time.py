"""Invented availability examples; no provider, model or private feature code."""
from dataclasses import dataclass
from datetime import datetime


def clock(value):
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None:raise ValueError('An explicit timezone is required')
    return result


@dataclass(frozen=True)
class Availability:
    published_upper_bound: str | None
    acquired_at: str
    status: str
    complete_report: bool=False


def views(observation: Availability | None, *, boundary: str, tip: str):
    cutoff,start=clock(boundary),clock(tip)
    if cutoff>=start:raise ValueError('A pregame boundary must precede tip')
    if observation is None:
        return dict(display='Unknown report coverage',source_supported=False,captured=False,healthy_claim=False)
    acquired=clock(observation.acquired_at)
    support=clock(observation.published_upper_bound) if observation.published_upper_bound else None
    source_supported=support is not None and support<=cutoff
    captured=acquired<=cutoff and (support is None or support<=cutoff)
    return dict(display=observation.status,source_supported=source_supported,captured=captured,
        healthy_claim=False,complete_reporting_scope=observation.complete_report)


def paired_changes(base,challenger):
    """Only exact shared game identities; the caller declares loss definition."""
    shared=sorted(base.keys() & challenger.keys())
    return dict(shared_games=shared,mean_loss_change=sum(challenger[k]-base[k] for k in shared)/len(shared) if shared else None,
        unmatched_base=sorted(base.keys()-challenger.keys()),unmatched_challenger=sorted(challenger.keys()-base.keys()))
