"""Invented calendar and price coverage, independent of forecast availability.

This public example has no real games, prices, forecasts, provider calls, fits,
orders or private research inputs. It composes the existing winner-reference
contract with a calendar census instead of using quoted games as an inventory.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
import json
from zoneinfo import ZoneInfo

from .contracts import timestamp
from .history_panels import POLICIES, PROVIDERS, reference_panel, validate


EVENT_FIELDS = {"data_kind", "event", "home", "away", "tip_at", "phase",
                "status", "schedule_observed_at", "has_saved_forecast"}
PHASES = {"preseason", "regular", "cup_final", "postseason", "unknown"}


def invented_event(**changes):
    row = dict(data_kind="INVENTED", event="invented-game-01", home="Blue",
               away="Gold", tip_at="2035-11-01T20:00:00Z", phase="regular",
               status="scheduled", schedule_observed_at="2035-10-31T12:00:00Z",
               has_saved_forecast=False)
    row.update(changes)
    return row


def validate_event(row):
    if set(row) != EVENT_FIELDS or row["data_kind"] != "INVENTED":
        raise ValueError("only allowlisted invented calendar records are supported")
    for key in ("event", "home", "away", "status"):
        if not isinstance(row[key], str) or not row[key].strip():
            raise ValueError("complete event and ordered-team identities required")
    if row["home"] == row["away"] or row["phase"] not in PHASES:
        raise ValueError("distinct ordered teams and an explicit phase required")
    if type(row["has_saved_forecast"]) is not bool:
        raise ValueError("forecast availability must be explicit")
    timestamp(row["tip_at"])
    timestamp(row["schedule_observed_at"])
    return deepcopy(row)


def reconcile_schedule(previous, fresh):
    """Retain absent games; record reschedules; reject changed ordered sides.

    A later observation can update the displayed schedule. It does not rewrite
    an old quote's tip clock or convert a pre-reschedule quote into a match.
    """
    selected, reschedules = {}, []
    for source in list(previous) + list(fresh):
        row = validate_event(source)
        old = selected.get(row["event"])
        if old:
            if (old["home"], old["away"]) != (row["home"], row["away"]):
                raise ValueError("same event with changed ordered sides requires reconciliation")
            old_clock, new_clock = timestamp(old["schedule_observed_at"]), timestamp(row["schedule_observed_at"])
            if new_clock == old_clock and row != old:
                raise ValueError("conflicting same-clock calendar versions")
            if new_clock <= old_clock:
                continue
            if timestamp(row["tip_at"]) != timestamp(old["tip_at"]):
                reschedules.append(dict(event=row["event"], previous_tip_at=old["tip_at"],
                    observed_tip_at=row["tip_at"], observed_at=row["schedule_observed_at"],
                    original_reference_clocks_unchanged=True))
            row["has_saved_forecast"] = row["has_saved_forecast"] or old["has_saved_forecast"]
        selected[row["event"]] = row
    return [selected[k] for k in sorted(selected)], reschedules


def pacific_date(tip_at):
    return timestamp(tip_at).astimezone(ZoneInfo("America/Los_Angeles")).date()


def pacific_week(tip_at):
    day = pacific_date(tip_at)
    return (day - timedelta(days=day.weekday())).isoformat()


def date_census(requested_dates, observations):
    """A successful empty day is distinct from an unobserved or failed day.

    Responses cover the dates actually requested, not an inferred full season.
    This example has no independent complete-season closure proof.
    """
    requested = list(requested_dates)
    if len(set(requested)) != len(requested):
        raise ValueError("requested dates must be unique")
    for day in requested:
        if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
            raise ValueError("canonical calendar dates required")
    observed = {}
    for row in observations:
        if set(row) != {"data_kind", "date", "status", "reported_games"} or row["data_kind"] != "INVENTED":
            raise ValueError("only invented date observations are supported")
        if row["date"] not in requested or row["date"] in observed:
            raise ValueError("date observations must uniquely match requested dates")
        if row["status"] not in {"OBSERVED", "SOURCE_FAILED"}:
            raise ValueError("explicit date source status required")
        games = row["reported_games"]
        if row["status"] == "OBSERVED":
            if type(games) is not int or games < 0:
                raise ValueError("observed day requires a nonnegative game count")
        elif games is not None:
            raise ValueError("failed date cannot claim zero games")
        observed[row["date"]] = deepcopy(row)
    rows = [observed.get(day, dict(data_kind="INVENTED", date=day,
            status="NOT_OBSERVED", reported_games=None)) for day in sorted(requested)]
    return dict(requested_dates=len(requested), observed_dates=sum(r["status"] == "OBSERVED" for r in rows),
                complete_requested_date_census=bool(rows) and all(r["status"] == "OBSERVED" for r in rows),
                complete_season_proven=False, dates=rows)


def build_board(events, observations):
    """Select references after collection and keep the entire game census.

    No outcome is accepted by the reference schema. Forecast availability is
    a display attribute and never filters acquisition or a coverage denominator.
    The inherited example supports home-side winner probabilities only.
    """
    observations = list(observations)
    events, _ = reconcile_schedule([], events)
    by_id = {row["event"]: row for row in events}
    joined, unjoined = [], []
    for source in observations:
        row = validate(source)
        game = by_id.get(row["event"])
        if game is None:
            unjoined.append(dict(row, reason="EVENT_OUTSIDE_OBSERVED_CALENDAR"))
        elif timestamp(row["tip_at"]) != timestamp(game["tip_at"]):
            unjoined.append(dict(row, reason="TIP_CLOCK_CHANGED_REQUIRES_REQUALIFICATION"))
        else:
            joined.append(row)
    selected = [row for policy in POLICIES for row in reference_panel(joined, policy)]
    output = [dict(game, pacific_date=pacific_date(game["tip_at"]).isoformat(),
                   pacific_week_start=pacific_week(game["tip_at"]),
                   references=[deepcopy(q) for q in selected if q["event"] == game["event"]])
              for game in events]
    coverage = []
    for provider in sorted(PROVIDERS):
        for policy in POLICIES:
            rows = [r for r in selected if r["provider"] == provider and r["quote_policy"] == policy]
            count = len({r["event"] for r in rows})
            coverage.append(dict(provider=provider, quote_policy=policy, inventory_games=len(events),
                observed_reference_games=count, missing_reference_games=len(events)-count,
                selected_contract_records=len(rows),
                historical_reference_games=len({r["event"] for r in rows if r["historical_reference_comparison_eligible"]}),
                original_possession_games=len({r["event"] for r in rows if r["original_possession_before_cutoff"]}),
                all_ticks_latest_proven_games=len({r["event"] for r in rows if r["latest_tick_exhaustiveness_proven"]})))
    return dict(data_kind="INVENTED", games=output, coverage=coverage, unjoined=unjoined,
                acquired_observation_records=len(observations), joined_observation_records=len(joined),
                source_completeness_proven=False, provider_requests=0, new_fits=0, new_forecasts=0,
                new_orders=0, allocation=0, profit=None, roi=None)


if __name__ == "__main__":
    from .history_panels import invented_quote
    print(json.dumps(build_board([invented_event(), invented_event(event="invented-game-02")],
                                [invented_quote()]), indent=2, sort_keys=True))
