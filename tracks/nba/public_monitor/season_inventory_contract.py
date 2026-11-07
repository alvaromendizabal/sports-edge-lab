"""NBA season display admission independent of model and provider availability.

This module contains no sports data or private deployment configuration. It
validates a supplied official inventory and attaches every supplied forecast and
provider observation without filtering games, choosing a model, filling a
missing value, or changing the original records.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
import math


ACTIVE_PROVIDERS = ("draftkings", "kalshi", "polymarket_us", "polymarket_international")
ARCHIVAL_PROVIDERS = ("market", "prizepicks", "underdog")
HORIZONS = ("opening", "latest_before_tip", "T60", "T120", "closing")
FORECAST_FIELDS = ("winner_prediction", "home_win_probability", "home_margin",
                   "home_cover_probability", "total_points")
PROBABILITY_FIELDS = ("home_win_probability", "home_cover_probability")


class InventoryContractError(ValueError):
    """The supplied evidence cannot support an unambiguous season display."""


def _require(condition, message):
    if not condition:
        raise InventoryContractError(message)


def _key(row):
    season, event = row.get("season"), row.get("event_id")
    _require(isinstance(season, str) and season.strip(), "season is required")
    _require(isinstance(event, str) and event.strip(), "event_id is required")
    return season, event


def _clock(value, field):
    _require(isinstance(value, str), field + " must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise InventoryContractError(field + " must be an ISO timestamp") from error
    _require(parsed.tzinfo is not None and parsed.utcoffset() is not None,
             field + " must include its timezone")
    return parsed


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _forecast(row, official):
    _require(row.get("horizon") in HORIZONS, "separate supported horizons are required")
    _require(isinstance(row.get("model_id"), str) and row["model_id"], "model_id is required")
    _require(row.get("evidence_kind") in ("issued", "retrospective", "early_outlook"),
             "issued, retrospective and early_outlook must remain distinguishable")
    missing = row.get("missing_reasons", {})
    _require(isinstance(missing, dict), "missing_reasons must be a mapping")
    for field in FORECAST_FIELDS:
        value = row.get(field)
        if value is None:
            _require(isinstance(missing.get(field), str) and missing[field].strip(),
                     "missing forecast field needs a concrete reason: " + field)
        elif field == "winner_prediction":
            _require(isinstance(value, str) and value.strip(), "winner_prediction must be a nonempty label")
        else:
            _require(_finite(value), "forecast value must be finite: " + field)
    for field in PROBABILITY_FIELDS:
        if row.get(field) is not None:
            _require(0 <= row[field] <= 1, "probability outside [0, 1]: " + field)
    if row.get("total_points") is not None:
        _require(row["total_points"] >= 0, "total_points must be nonnegative")
    if row.get("home_cover_probability") is not None:
        _require(_finite(row.get("home_spread_line")), "cover probability requires its exact home spread line")
    if row.get("evidence_kind") == "issued":
        issue = _clock(row.get("issued_at_utc"), "issued_at_utc")
        tip = _clock(official.get("tip_at_utc"), "tip_at_utc")
        _require(issue < tip, "an issued pregame record must precede official tip")
        if row["horizon"] in ("T60", "T120"):
            minutes = 60 if row["horizon"] == "T60" else 120
            _require((tip - issue).total_seconds() >= minutes * 60,
                     "issued record falls after its declared horizon cutoff")
        _require(isinstance(row.get("issue_hash"), str) and row["issue_hash"],
                 "an issued record requires its immutable issue hash")
    if row.get("training_cutoff_utc") is not None:
        training = _clock(row["training_cutoff_utc"], "training_cutoff_utc")
        origin = _clock(row.get("origin_at_utc"), "origin_at_utc")
        _require(training <= origin, "training cutoff follows model origin")


def _provider_observation(row):
    status = row.get("availability")
    _require(status in ("observed", "unavailable"), "provider availability must be explicit")
    if status == "unavailable":
        _require(isinstance(row.get("missing_reason"), str) and row["missing_reason"].strip(),
                 "unavailable product requires its concrete missing reason")
        return
    _require(row.get("representation") in ("contract_probability", "implied_probability", "decimal_price", "point_line"),
             "observed provider value requires its representation")
    _require(_finite(row.get("value")), "observed provider value must be finite")
    if row["representation"] in ("contract_probability", "implied_probability"):
        _require(0 <= row["value"] <= 1, "provider probability outside [0, 1]")
    elif row["representation"] == "decimal_price":
        _require(row["value"] > 1, "decimal price must exceed one")
    _clock(row.get("acquired_at_utc"), "acquired_at_utc")
    _require(row.get("possession_kind") in ("original", "later_retrieval"),
             "later retrieval must remain distinct from original possession")


def reconcile_season_inventory(official_games, forecast_rows=(), provider_rows=()):
    """Return every supplied official event plus explicit coverage accounting.

    Official inventory is the only source of board membership. Rows that cannot
    be joined are returned in an orphan report; they cannot silently create or
    remove official events. The caller remains responsible for authenticating
    the completeness and clocks of the official inventory itself.
    """
    inventory = {}
    order = []
    for supplied in official_games:
        row = deepcopy(supplied)
        key = _key(row)
        _require(key not in inventory, "duplicate official event requires explicit revision reconciliation")
        inventory[key] = row
        order.append(key)
    forecasts, providers = defaultdict(list), defaultdict(list)
    orphans = {"forecasts": [], "providers": []}
    for supplied in forecast_rows:
        row = deepcopy(supplied)
        key = _key(row)
        if key not in inventory:
            orphans["forecasts"].append(row)
            continue
        _forecast(row, inventory[key])
        forecasts[key].append(row)
    for supplied in provider_rows:
        row = deepcopy(supplied)
        key = _key(row)
        _require(row.get("provider") in ACTIVE_PROVIDERS + ARCHIVAL_PROVIDERS,
                 "provider identity must distinguish US, international and archival sources")
        _require(row.get("horizon") in HORIZONS, "provider horizon is required")
        _require(row.get("product") in ("winner", "spread", "total"), "provider product is required")
        _provider_observation(row)
        if key not in inventory:
            orphans["providers"].append(row)
            continue
        providers[key].append(row)
    board = []
    coverage = Counter()
    for key in order:
        attached_forecasts, attached_providers = forecasts[key], providers[key]
        active = [r for r in attached_providers if r["provider"] in ACTIVE_PROVIDERS]
        archival = [r for r in attached_providers if r["provider"] in ARCHIVAL_PROVIDERS]
        missing_fields = [field for field in FORECAST_FIELDS
                          if not any(r.get(field) is not None for r in attached_forecasts)]
        missing_products = []
        for provider in ACTIVE_PROVIDERS:
            for product in ("winner", "spread", "total"):
                for horizon in HORIZONS:
                    matched = [r for r in active if (r["provider"], r["product"], r["horizon"])
                               == (provider, product, horizon)]
                    if any(r["availability"] == "observed" for r in matched):
                        continue
                    reasons = list(dict.fromkeys(r["missing_reason"] for r in matched
                                                 if r["availability"] == "unavailable"))
                    if not reasons:
                        reasons = ["NO_MATCHED_OBSERVATION_IN_SUPPLIED_INPUT"]
                    missing_products.append({"provider": provider, "product": product, "horizon": horizon,
                                             "reason": reasons[0] if len(reasons) == 1 else "MULTIPLE_RETAINED_REASONS",
                                             "reasons": reasons})
        board.append({"official": inventory[key], "forecasts": attached_forecasts,
                      "providers": active, "archival_providers": archival,
                      "missing_forecast_fields": missing_fields,
                      "missing_provider_products": missing_products})
        coverage[key[0]] += 1
    return {"schema": "nba.season_inventory_contract.v1", "board": board,
            "official_events_by_season": dict(coverage), "official_events": len(inventory),
            "displayed_events": len(board), "omitted_official_events": 0,
            "official_inventory_completeness_asserted": False, "orphan_records": orphans,
            "missing_predictions_or_quotes_filter_events": False}


def comparison_key(row):
    """Exact pairing dimensions; a contract probability is never a point mean."""
    fields = ("season", "event_id", "side", "target", "line", "horizon", "product", "method", "settlement")
    _key(row)
    _require(all(field in row for field in fields), "comparison lacks an explicit pairing dimension")
    for field in fields:
        if field != "line":
            _require(isinstance(row[field], str) and row[field].strip(),
                     "comparison dimension must be a nonempty string: " + field)
    _require(row["horizon"] in HORIZONS, "comparison horizon is not supported")
    if row["product"] == "point_prediction" and row["target"] in ("margin", "total"):
        _require(row.get("representation") in ("point_mean", "point_median", "point_quantile")
                 and row["method"] not in ("binary_contract", "contract_probability", "implied_probability"),
                 "binary contract or implied probabilities are not point predictions")
        _require(row["line"] is None, "point prediction comparison must explicitly use line=None")
    elif row["target"] in ("margin", "total", "cover_probability"):
        _require(_finite(row["line"]), "line-based comparison requires an exact line")
    else:
        _require(row["line"] is None or _finite(row["line"]), "comparison line must be finite or explicitly None")
    return tuple(row[field] for field in fields)
