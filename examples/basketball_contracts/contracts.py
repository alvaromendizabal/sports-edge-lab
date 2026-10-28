"""Small public contracts for reviewing basketball forecast provenance.

These generic checks are separate from private acquisition, feature recipes and
fitted models. They make no network calls, fit no models and send no orders.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import json
import math
from typing import Iterable


class League(str, Enum):
    NBA = "nba"
    NCAAM = "ncaam"
    NCAAW = "ncaaw"


def utc(value: str | datetime) -> datetime:
    """Require an actual timezone; a date or naive timestamp is insufficient."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if not isinstance(parsed, datetime) or parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("A timezone-aware timestamp is required")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class Identity:
    league: League
    provider: str
    kind: str
    native_id: str

    def __post_init__(self):
        if not isinstance(self.league, League):
            raise ValueError("League must be an explicit supported namespace")
        if self.kind not in {"event", "team", "player"}:
            raise ValueError("Unsupported identity kind")
        if not self.provider or not self.native_id or any(":" in item for item in (self.provider, self.native_id)):
            raise ValueError("Provider and native IDs must be nonempty atomic values")

    def __str__(self):
        return ":".join((self.league.value, self.provider, self.kind, self.native_id))


@dataclass(frozen=True)
class Game:
    event: Identity
    home: Identity
    away: Identity
    tipoff: datetime
    season_start_year: int
    season_end_year: int
    game_type: str
    neutral: bool | None

    def __post_init__(self):
        if self.event.kind != "event" or self.home.kind != "team" or self.away.kind != "team":
            raise ValueError("Event and team identity kinds cannot be interchanged")
        if len({self.event.league, self.home.league, self.away.league}) != 1:
            raise ValueError("A game cannot mix league namespaces")
        if self.home == self.away:
            raise ValueError("The two teams must differ")
        utc(self.tipoff)
        if self.season_end_year != self.season_start_year + 1:
            raise ValueError("Basketball seasons retain explicit start and ending years")
        if self.game_type not in {"regular", "postseason", "unverified", "excluded"}:
            raise ValueError("Unknown game-type label")
        if self.neutral is not None and type(self.neutral) is not bool:
            raise ValueError("Neutral status is true, false or unknown")

    def cutoff(self, minutes_before: int) -> datetime:
        if type(minutes_before) is not int or minutes_before <= 0:
            raise ValueError("The pregame horizon must be a positive integer")
        return utc(self.tipoff) - timedelta(minutes=minutes_before)


@dataclass(frozen=True)
class SourceEvidence:
    content_sha256: str
    retrieved_at: datetime
    first_observed_at: datetime | None
    published_at: datetime | None
    revised_at: datetime | None

    def __post_init__(self):
        if len(self.content_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.content_sha256):
            raise ValueError("An exact SHA-256 content identity is required")
        retrieval = utc(self.retrieved_at)
        for clock in (self.first_observed_at, self.published_at, self.revised_at):
            if clock is not None:
                utc(clock)
        if self.first_observed_at is not None and utc(self.first_observed_at) > retrieval:
            raise ValueError("First observation cannot be later than this retrieval")
        if self.revised_at is not None and self.published_at is not None and utc(self.revised_at) < utc(self.published_at):
            raise ValueError("Revision cannot precede publication")

    def evidence_tier(self, cutoff: datetime, *, assumed_available_at: datetime | None = None) -> str:
        boundary = utc(cutoff)
        clocks = (self.published_at, self.first_observed_at)
        known_before = all(clock is not None and utc(clock) <= boundary for clock in clocks)
        revision_before = self.revised_at is None or utc(self.revised_at) <= boundary
        if known_before and revision_before:
            return "strict_point_in_time"
        if assumed_available_at is not None and utc(assumed_available_at) <= boundary:
            return "reconstructed_research"
        return "inadmissible_or_unknown"


@dataclass(frozen=True)
class QuoteEvidence:
    event: Identity
    cutoff: datetime
    snapshot_at: datetime
    quote_updated_at: datetime
    observed_at: datetime
    target: str = "game_winner_including_overtime"
    label: str = "MARKET"

    def eligible(self, *, freshness_minutes=15) -> bool:
        if self.event.kind != "event" or self.label != "MARKET":
            return False
        cutoff, snapshot = utc(self.cutoff), utc(self.snapshot_at)
        updated, observed = utc(self.quote_updated_at), utc(self.observed_at)
        if freshness_minutes <= 0:
            raise ValueError("Freshness must be positive")
        # Observation may be a later retrieval from a provider archive. It does
        # not make that price a historical fill or an archived live forecast.
        return updated <= snapshot <= cutoff and updated <= observed and timedelta() <= cutoff - updated <= timedelta(minutes=freshness_minutes)


@dataclass(frozen=True)
class SelectionPolicy:
    historical_validation_seasons: tuple[int, ...] = (2025, 2026)
    protected_season: int = 2027

    def validate_selection(self, seasons: Iterable[int]):
        observed = tuple(seasons)
        if not observed:
            raise ValueError("No historical selection evidence")
        if any(type(season) is not int or season >= self.protected_season for season in observed):
            raise ValueError("Current/future season outcomes cannot select the recipe")
        if any(season >= self.protected_season for season in self.historical_validation_seasons):
            raise ValueError("The frozen validation plan crosses the protected boundary")

    def validate_fold(self, train_seasons: Iterable[int], validation_season: int):
        training = tuple(train_seasons)
        self.validate_selection((*training, validation_season))
        if not training or max(training) >= validation_season:
            raise ValueError("Training must precede its validation season")
        if validation_season not in self.historical_validation_seasons:
            raise ValueError("Validation season is outside the declared plan")


@dataclass(frozen=True)
class ScoredForecast:
    event: Identity
    cutoff: datetime
    probability: float
    observed_outcome: int
    target: str = "game_winner_including_overtime"

    def __post_init__(self):
        utc(self.cutoff)
        if self.event.kind != "event" or not math.isfinite(self.probability) or not 0 <= self.probability <= 1:
            raise ValueError("Invalid event/probability")
        if type(self.observed_outcome) is not int or self.observed_outcome not in {0, 1}:
            raise ValueError("A completed binary outcome is required for scoring")


def matched_brier(model: Iterable[ScoredForecast], market: Iterable[ScoredForecast]) -> dict:
    """Score identical event/horizon/target cohorts, aligned by native identity."""
    left, right = tuple(model), tuple(market)
    a, b = {str(row.event): row for row in left}, {str(row.event): row for row in right}
    if not a or len(a) != len(left) or len(b) != len(right) or set(a) != set(b):
        raise ValueError("Comparisons require the same nonempty unique event cohort")
    leagues = {row.event.league for row in left + right}
    if len(leagues) != 1:
        raise ValueError("Report each basketball league separately")
    for key in a:
        x, y = a[key], b[key]
        if utc(x.cutoff) != utc(y.cutoff) or x.target != y.target or x.observed_outcome != y.observed_outcome:
            raise ValueError("Event cutoff, target and outcome must match")
    def score(values):
        return sum((row.probability - row.observed_outcome) ** 2 for row in values) / len(values)
    return {"league": next(iter(leagues)).value, "games": len(a),
            "synthetic_model_brier": score(left), "MARKET_brier": score(right),
            "cohort_sha256": hashlib.sha256(json.dumps(sorted(a), separators=(",", ":")).encode()).hexdigest(),
            "profit": None, "profit_status": "unavailable_without_predecision_execution_and_settlement_evidence"}
