"""Validate a sanitized current-only native display, not a forecast or feed.

This public contract consumes rounded reporting values and preserves missing
products. It contains no raw provider payload, private model, credential or
acquisition logic. Hashes and this validator do not authenticate a provider.
"""
from collections import Counter
import math

from .market_time import instant

REGISTRATION = "CURRENT_SNAPSHOT_ONLY"
SCHEMA = "fbs.public.verified-native-current-snapshot.v1"
PROVIDERS = ("Kalshi", "Polymarket Global", "Polymarket US")
TARGETS = ("winner", "margin", "total")
WINNER = "PRE_KICKOFF_CAPTURE_BID_ASK_MIDPOINT_NOT_FINAL_QUOTE"
BOUNDS = "BOUNDED_QUOTED_MEDIAN_INTERVAL"
MISSING = "NO_EXACT_BOUND_NATIVE_PRODUCT_IN_VERIFIED_SUBSET"
POSTGAME = "ONLY_POST_KICKOFF_CURRENT_CAPTURE_NOT_PREGAME_HISTORY"
INCONSISTENT = "INCONSISTENT_QUOTED_THRESHOLD_CURVE"
UNUSABLE = "CATALOG_PRESENT_NO_USABLE_PREGAME_QUOTE"
STATUSES = {WINNER, BOUNDS, MISSING, POSTGAME, INCONSISTENT, UNUSABLE}
ROOT_KEYS = {
    "captured_at_max", "captured_at_min", "expected_margin_or_total_invented",
    "genuine_forecasts_issued", "inconsistent_us_margin_groups", "inconsistent_us_total_groups",
    "individual_quote_clock_proved", "latest_pre_kickoff_history_complete", "model_input_admitted",
    "official_current_week_games", "orders", "phase", "point_basis", "product_slots", "quote_at",
    "registered_cutoff_kind", "schema", "season", "slots", "source_release",
    "source_time_not_replaced_with_review_time", "stake_usd", "status_counts",
    "us_literal_side_prices_and_quotes_not_used_as_book", "view", "week", "winner_basis",
}
SLOT_KEYS = {"captured_at", "game_id", "lower_bound", "observed_contracts", "p_home", "provider",
             "quote_at", "status", "support_available_at", "target", "upper_bound"}


def require(value, message):
    if not value:
        raise ValueError(message)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_snapshot(snapshot, games, *, prepared_at, current_week):
    """Require every game/provider/product slot and exact reference closure.

    A missing latest slot cannot be replaced with an earlier snapshot. Current
    captures do not qualify the source-timed T120/T60/latest-history panels.
    Point intervals describe quoted medians, never expected score estimates.
    """
    if snapshot is None:
        require(not any(r.get("registered_cutoff_kind") == REGISTRATION
                        for g in games for refs in g["markets"].values() for r in refs),
                "Current-only references require the complete explicit slot grid")
        return None
    require(isinstance(snapshot, dict) and set(snapshot) == ROOT_KEYS and snapshot["schema"] == SCHEMA,
            "Unknown native current snapshot field or schema")
    require(snapshot["source_release"] == "V030" and snapshot["view"] == "current"
            and snapshot["registered_cutoff_kind"] == REGISTRATION and snapshot["quote_at"] is None,
            "Native display cannot become historical quote evidence")
    for flag in ("expected_margin_or_total_invented", "individual_quote_clock_proved",
                 "latest_pre_kickoff_history_complete", "model_input_admitted"):
        require(snapshot[flag] is False, "Native snapshot cannot admit model/history/mean claims")
    for flag in ("source_time_not_replaced_with_review_time", "us_literal_side_prices_and_quotes_not_used_as_book"):
        require(snapshot[flag] is True, "Native source-clock and typed-price qualification must remain")
    for key in ("genuine_forecasts_issued", "orders", "stake_usd"):
        require(type(snapshot[key]) is int and snapshot[key] == 0, "Display cannot issue forecasts or wagers")
    begin, end = instant(snapshot["captured_at_min"]), instant(snapshot["captured_at_max"])
    require(begin <= end <= instant(prepared_at), "Native capture cannot be rewritten to a later review or future")
    lo, hi = instant(current_week["start_inclusive_utc"]), instant(current_week["end_exclusive_utc"])
    scoped = {g["id"]: g for g in games if lo <= instant(g["kickoff"]) < hi}
    require(snapshot["official_current_week_games"] == len(scoped)
            and snapshot["product_slots"] == len(scoped) * len(PROVIDERS) * len(TARGETS),
            "Native current inventory denominator differs")
    require(all(g["season"] == snapshot["season"] and g["phase"] == snapshot["phase"]
                and g["week"] == snapshot["week"] for g in scoped.values()), "Native current calendar identity differs")
    expected = {(gid, provider, target) for gid in scoped for provider in PROVIDERS for target in TARGETS}
    require(isinstance(snapshot["slots"], list), "Native slot grid missing")
    seen, counts, clocks = set(), Counter(), []
    refs = {}
    for g in games:
        for provider, records in g["markets"].items():
            for row in records:
                if row.get("registered_cutoff_kind") != REGISTRATION:
                    continue
                key = (g["id"], provider, row["target"])
                require(key not in refs, "Duplicate latest native product reference")
                refs[key] = row
    for slot in snapshot["slots"]:
        require(isinstance(slot, dict) and set(slot) == SLOT_KEYS, "Unknown native product slot field")
        key = slot["game_id"], slot["provider"], slot["target"]
        require(key in expected and key not in seen, "Native grid has missing, duplicate or foreign identity")
        seen.add(key)
        status = slot["status"]
        require(status in STATUSES and slot["quote_at"] is None, "Unknown native state or invented quote clock")
        require(type(slot["observed_contracts"]) is int and slot["observed_contracts"] >= 0,
                "Observed contracts must not be invented from status")
        counts[f'{slot["provider"]}:{slot["target"]}:{status}'] += 1
        row = refs.get(key)
        if status == MISSING:
            require(slot["observed_contracts"] == 0 and row is None
                    and all(slot[x] is None for x in ("captured_at", "p_home", "lower_bound", "upper_bound", "support_available_at")),
                    "Missing native product cannot acquire a quote, clock or fallback reference")
            continue
        require(slot["observed_contracts"] > 0 and slot["captured_at"] is not None and row is not None,
                "Observed native slot requires its actual capture and reference")
        captured = instant(slot["captured_at"])
        clocks.append(captured)
        require(begin <= captured <= end, "Native per-product capture lies outside source capture range")
        require(row["captured_at"] == slot["captured_at"] and row["quote_at"] is None
                and row["price_status"] == status and row["source_query_cutoff_kind"] == "current"
                and row["product"] == "verified_native_current_snapshot"
                and row["evidence_kind"] == "current_public_observation" and row["executable"] is False,
                "Native reference and complete-grid identity or clock differ")
        kick = instant(scoped[slot["game_id"]]["kickoff"])
        if status == WINNER:
            require(slot["target"] == "winner" and finite(slot["p_home"]) and 0 <= slot["p_home"] <= 1
                    and row["value"] == slot["p_home"] and row["picked_home"] == (slot["p_home"] >= .5)
                    and row["point_support"] is None and captured < kick,
                    "Native winner is not an authenticated pregame display probability")
            require(all(slot[x] is None for x in ("lower_bound", "upper_bound", "support_available_at")),
                    "Winner snapshot cannot become a point estimate")
        elif status == BOUNDS:
            support = row["point_support"]
            require(slot["target"] in ("margin", "total") and slot["p_home"] is None
                    and row["value"] is None and row["picked_home"] is None
                    and finite(slot["lower_bound"]) and finite(slot["upper_bound"])
                    and slot["lower_bound"] < slot["upper_bound"] and captured < kick,
                    "Native median interval cannot become an invented scalar or crossing interval")
            require(isinstance(support, dict) and support["lower_bound"] == slot["lower_bound"]
                    and support["upper_bound"] == slot["upper_bound"]
                    and support["support_available_at"] == slot["support_available_at"]
                    and begin <= instant(slot["support_available_at"]) <= captured,
                    "Native support bounds or availability differ from the grid")
        else:
            require(all(slot[x] is None for x in ("p_home", "lower_bound", "upper_bound", "support_available_at"))
                    and row["value"] is None and row["picked_home"] is None,
                    "Unavailable native state cannot retain a usable old or invented value")
            if status == POSTGAME:
                require(captured >= kick, "Postgame classification must retain its actual clock")
            if status == INCONSISTENT:
                require(slot["provider"] == "Polymarket US" and slot["target"] in ("margin", "total"),
                        "Inconsistent curve state requires its exact native product")
    require(seen == expected and len(snapshot["slots"]) == snapshot["product_slots"],
            "Native complete slot grid lost games/products")
    require(dict(counts) == snapshot["status_counts"], "Native status counts differ from retained slots")
    require(clocks and min(clocks) == begin and max(clocks) == end, "Native source range does not close")
    for target in ("margin", "total"):
        require(snapshot[f"inconsistent_us_{target}_groups"] == counts[f"Polymarket US:{target}:{INCONSISTENT}"],
                "Native inconsistent-curve accounting differs")
    return snapshot
