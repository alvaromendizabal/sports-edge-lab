"""Generic historical-selection boundary, using invented demonstration scores.

This educational rule is not the private football selection policy. Monitoring
observations have no argument through which to influence ``select_historical``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import math


@dataclass(frozen=True)
class SelectionContract:
    candidates: tuple[str, ...]
    historical_seasons: tuple[int, ...]
    forward_first_season: int
    protocol: str
    frozen_at: datetime
    reference: str = "MARKET"


@dataclass(frozen=True)
class HistoricalScore:
    candidate: str
    season: int
    protocol: str
    cohort: str
    games: int
    log_loss: float
    brier: float
    paired_log_loss_upper: float
    labels_available_at: datetime
    training_last_season: int


def _aware(value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone-aware clock required")


def _finite(value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("finite numerical metric required")


def select_historical(contract: SelectionContract, rows: tuple[HistoricalScore, ...]) -> dict:
    """Select from exact historical panels; later rows are rejected, not ignored.

    The illustrative decision requires each season's loss, Brier and supplied
    paired upper bound to support a candidate. Eligible candidates are ordered by
    equal-season mean loss with a stable identifier tie-break. A supplied interval
    is not recomputed or certified from these aggregates.
    """
    _aware(contract.frozen_at)
    if (not contract.candidates or any(not isinstance(c,str) or not c for c in contract.candidates)
            or len(set(contract.candidates)) != len(contract.candidates)
            or contract.reference not in contract.candidates):
        raise ValueError("unique declared candidates including reference required")
    seasons = contract.historical_seasons
    if (type(contract.forward_first_season) is not int or not seasons or len(set(seasons)) != len(seasons)
            or any(type(s) is not int or s >= contract.forward_first_season for s in seasons)):
        raise ValueError("historical seasons must precede the forward season")
    if contract.protocol not in {"fixed", "annual", "precommitted_online"}:
        raise ValueError("one explicit update protocol required")
    expected = {(candidate, season) for candidate in contract.candidates for season in seasons}
    indexed = {}
    for row in rows:
        key = (row.candidate, row.season)
        if type(row.season) is not int or key not in expected or key in indexed:
            raise ValueError("undeclared, forward, or duplicate selection row")
        if row.protocol != contract.protocol:
            raise ValueError("update policies cannot be pooled silently")
        if (not row.cohort or type(row.games) is not int or row.games < 1
                or type(row.training_last_season) is not int or row.training_last_season >= row.season):
            raise ValueError("invalid chronological score identity")
        for value in (row.log_loss, row.brier, row.paired_log_loss_upper):
            _finite(value)
        if row.log_loss < 0 or not 0 <= row.brier <= 1:
            raise ValueError("metric outside its domain")
        _aware(row.labels_available_at)
        if row.labels_available_at > contract.frozen_at:
            raise ValueError("selection uses unavailable labels")
        indexed[key] = row
    if set(indexed) != expected:
        raise ValueError("complete candidate by season panel required")
    for season in seasons:
        if len({(indexed[c, season].cohort, indexed[c, season].games) for c in contract.candidates}) != 1:
            raise ValueError("exact matched cohorts required")
    candidates = []
    for candidate in contract.candidates:
        own = [indexed[candidate, season] for season in seasons]
        baseline = [indexed[contract.reference, season] for season in seasons]
        eligible = candidate == contract.reference or all(
            a.log_loss < b.log_loss and a.brier <= b.brier and a.paired_log_loss_upper < 0
            for a, b in zip(own, baseline))
        candidates.append({"candidate": candidate, "historically_eligible": eligible,
                           "equal_season_log_loss": math.fsum(r.log_loss for r in own) / len(own)})
    chosen = min((r for r in candidates if r["historically_eligible"]),
                 key=lambda r: (r["equal_season_log_loss"], r["candidate"]))["candidate"]
    evidence = {"contract": asdict(contract), "scores": [asdict(indexed[k]) for k in sorted(indexed)]}
    encoded = json.dumps(evidence, default=lambda x: x.isoformat(), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    record = {"selected": chosen, "candidates": candidates, "historical_seasons": list(seasons),
            "protocol": contract.protocol, "forward_first_season": contract.forward_first_season,
            "evidence_sha256": hashlib.sha256(encoded).hexdigest(),
            "current_season_outcomes_used": False, "demonstration_only": True}
    identity = hashlib.sha256(json.dumps(record,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    return {**record,"selection_sha256":identity}


def monitor_frozen_selection(selection: dict, observations: tuple[dict, ...]) -> dict:
    """Return monitoring in declared candidate order, without changing selection."""
    body={k:v for k,v in selection.items()if k!='selection_sha256'}
    if hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()!=selection.get('selection_sha256'):
        raise ValueError("frozen selection record changed")
    order = [r["candidate"] for r in selection["candidates"]]
    seen = set()
    for row in observations:
        if set(row) != {"candidate", "season", "log_loss"}:
            raise ValueError("monitoring schema differs")
        if row["candidate"] not in order or row["candidate"] in seen:
            raise ValueError("undeclared or duplicate monitoring candidate")
        if type(row["season"]) is not int or row["season"] < selection["forward_first_season"]:
            raise ValueError("historical rows do not belong in forward monitoring")
        _finite(row["log_loss"])
        if row["log_loss"] < 0:
            raise ValueError("negative log loss")
        seen.add(row["candidate"])
    return {"selected": selection["selected"], "selection_sha256": selection["selection_sha256"],
            "monitoring_only": True, "ranked_by_forward_outcome": False,
            "observations": sorted(observations, key=lambda row: order.index(row["candidate"]))}


def demonstration() -> dict:
    from datetime import timezone
    clock = datetime(2022, 2, 1, tzinfo=timezone.utc)
    contract = SelectionContract(("MARKET", "stable", "unstable"), (2020, 2021), 2022, "annual", clock)
    rows = tuple(HistoricalScore(c, s, "annual", f"invented-{s}", 100,
        loss, brier, upper, clock, s-1)
        for c, scores in (("MARKET", ((.61,.21,0),(.60,.20,0))),
                          ("stable", ((.58,.19,-.01),(.57,.18,-.01))),
                          ("unstable", ((.54,.18,-.02),(.63,.22,.03))))
        for s, (loss,brier,upper) in zip((2020,2021),scores))
    selection = select_historical(contract, rows)
    monitoring = monitor_frozen_selection(selection, tuple(
        {"candidate": c, "season": 2022, "log_loss": loss}
        for c, loss in (("MARKET",.60),("stable",.62),("unstable",.40))))
    return {"synthetic_only": True, "selection": selection, "monitoring": monitoring}


if __name__ == "__main__":
    print(json.dumps(demonstration(), indent=2))
