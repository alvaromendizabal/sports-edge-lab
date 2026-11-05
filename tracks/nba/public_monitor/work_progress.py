"""Credential-free progress contracts, illustrated with invented work only.

Request attempts, heartbeats and selected candidates are not verified data.
The records contain no provider endpoint, private recipe or real-run counters.
"""
from dataclasses import dataclass
from datetime import datetime
from math import isfinite


@dataclass(frozen=True)
class Snapshot:
    phase: str
    observed_at: str
    attempts: int
    successful_responses: int
    errors: int
    completed_items: int
    remaining_items: int
    verified_new_rows: int
    covered_games: int
    discovery_exhausted: bool = False
    comparable_item_cost: bool = False
    cooldown_until: str | None = None

    def __post_init__(self):
        clock = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        if clock.tzinfo is None:
            raise ValueError("An aware observation clock is required")
        for field in ("attempts", "successful_responses", "errors", "completed_items",
                      "remaining_items", "verified_new_rows", "covered_games"):
            if type(getattr(self, field)) is not int or getattr(self, field) < 0:
                raise ValueError("Counters must be nonnegative integers")
        if self.successful_responses + self.errors > self.attempts:
            raise ValueError("Response accounting exceeds actual attempts")
        if self.cooldown_until:
            until = datetime.fromisoformat(self.cooldown_until.replace("Z", "+00:00"))
            if until.tzinfo is None:
                raise ValueError("An aware cooldown clock is required")


def compare(current: Snapshot, previous: Snapshot | None = None) -> dict:
    """Derive interval progress without carrying fields from an earlier phase."""
    result = {"phase": current.phase, "verified_new_rows": current.verified_new_rows,
              "covered_games": current.covered_games, "remaining_items": current.remaining_items,
              "successful_responses": current.successful_responses, "errors": current.errors,
              "cooldown_until": current.cooldown_until, "rows_per_second": None,
              "eta_seconds": None, "eta_status": "NOT_ESTIMABLE",
              "meaningful_interval_progress": None}
    if previous is None or previous.phase != current.phase:
        return result
    elapsed = (datetime.fromisoformat(current.observed_at.replace("Z", "+00:00")) -
               datetime.fromisoformat(previous.observed_at.replace("Z", "+00:00"))).total_seconds()
    if not isfinite(elapsed) or elapsed <= 0:
        raise ValueError("Observation clocks must advance")
    for field in ("attempts", "successful_responses", "errors", "completed_items",
                  "verified_new_rows", "covered_games"):
        if getattr(current, field) < getattr(previous, field):
            raise ValueError("A cumulative phase counter moved backwards")
    rows = current.verified_new_rows - previous.verified_new_rows
    games = current.covered_games - previous.covered_games
    items = current.completed_items - previous.completed_items
    result["rows_per_second"] = rows / elapsed
    result["meaningful_interval_progress"] = rows > 0 or games > 0
    if (items > 0 and current.discovery_exhausted and current.comparable_item_cost
            and current.cooldown_until is None):
        result["eta_seconds"] = elapsed * current.remaining_items / items
        result["eta_status"] = "CONDITIONAL_ENUMERATED_COMPARABLE_ITEMS_ONLY"
    return result


def select_phase(*, current_inventory_disposed: bool, priority_budget_exhausted: bool,
                 priority_work_remaining: bool, model_report_finished: bool) -> str:
    """A known backlog cannot indefinitely block the next research/report phase."""
    if not current_inventory_disposed:
        return "CURRENT_INVENTORY_WITH_EXPLICIT_SOURCE_GAPS"
    if priority_work_remaining and not priority_budget_exhausted:
        return "PRIORITY_REFERENCES"
    if not model_report_finished:
        return "MODEL_AND_REPORT"
    return "BOUNDED_HISTORY_WITH_RETAINED_BACKLOG"
