"""Render the NBA board from an already sanitized public projection.

This module does not read private owner archives, fit models, collect prices, or
change source/issue clocks. Public role aliases are the only model identifiers.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "tracks/nba/current/board.json"
TEMPLATE = Path(__file__).with_name("spread_totals_template.html")
OUTPUT = ROOT / "docs/nba/spread-totals"


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_week_calendar(data):
    """Keep a later weekly status check separate from saved research evidence."""
    calendar = data.get("latest_week_calendar")
    observed = [game for game in data["games"] if "calendar_observation" in game]
    if calendar is None:
        if observed:
            raise ValueError("weekly calendar summary required")
        return
    if calendar.get("schema") != "public.nba.week_calendar.v1" or calendar.get("observation_scope") != "WEEK_ONLY":
        raise ValueError("weekly calendar scope required")
    for key in ("forecast_inputs_refreshed", "forecasts_reissued", "full_season_census_refreshed"):
        if calendar.get(key) is not False:
            raise ValueError("weekly calendar cannot claim forecast or season research refresh")
    if calendar.get("new_fits") != 0 or calendar.get("model_inference_calls") != 0:
        raise ValueError("weekly calendar contains no fitting or model inference")
    if calendar.get("date_coverage_complete") is not True or calendar.get("game_team_and_tip_identity_unchanged") is not True:
        raise ValueError("weekly calendar exact date and game identity required")
    week = [game for game in data["games"] if game["in_week"]]
    expected_ids = {game["game_id"] for game in week}
    if len(observed) != len(week) or {game["game_id"] for game in observed} != expected_ids:
        raise ValueError("weekly calendar must cover exactly the full saved week")
    if calendar.get("game_ids") != sorted(expected_ids) or calendar.get("observed_games") != len(week):
        raise ValueError("weekly calendar denominator differs")
    if any(calendar.get(key) != data[key] for key in ("week_start_pacific", "week_end_pacific")):
        raise ValueError("weekly calendar date window differs")
    start, end = (datetime.fromisoformat(data[key]).date() for key in ("week_start_pacific", "week_end_pacific"))
    dates = [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]
    counts = {date: sum(game["pacific_date"] == date for game in week) for date in dates}
    requested_dates = calendar.get("requested_date_count", calendar.get("official_requests"))
    if calendar.get("date_game_counts") != counts or requested_dates != len(dates):
        raise ValueError("weekly calendar includes every date, including empty dates")
    if type(calendar.get("official_requests")) is not int or calendar["official_requests"] < 0:
        raise ValueError("weekly calendar request accounting required")
    if calendar.get("source_urls") != ["https://www.nba.com/games?date=" + date for date in dates]:
        raise ValueError("official weekly date sources required")
    checked = parse_time(calendar["checked_at_utc"])
    saved = parse_time(data["source_observed_at_utc"])
    if checked.tzinfo is None or checked < saved:
        raise ValueError("weekly calendar observation clock is older than saved census")
    final = updated = 0
    statuses = Counter()
    for game in observed:
        row = game["calendar_observation"]
        if row.get("observation_scope") != "WEEK_ONLY" or any(row.get(key) != game[key] for key in ("game_id", "home_abbr", "away_abbr")):
            raise ValueError("weekly calendar game identity differs")
        if parse_time(row["tip_at_utc"]) != parse_time(game["tip_at_utc"]):
            raise ValueError("weekly calendar cannot rebind a saved forecast tip time")
        source_clock = parse_time(row["source_checked_at_utc"])
        if source_clock.tzinfo is None or not saved <= source_clock <= checked:
            raise ValueError("weekly calendar per-game clock is outside its observed interval")
        if row.get("source_url") != "https://www.nba.com/games?date=" + game["pacific_date"]:
            raise ValueError("weekly calendar source date differs")
        if row.get("status") not in {"FINAL", "SCHEDULED", "LIVE", "POSTPONED", "CANCELED", "SUSPENDED", "UNAVAILABLE"} or row.get("completed") is not (row["status"] == "FINAL"):
            raise ValueError("weekly calendar status is inconsistent")
        statuses[row["status"]] += 1
        scores = (row.get("away_score"), row.get("home_score"))
        if row["completed"]:
            if parse_time(game["tip_at_utc"]) >= source_clock or any(type(score) is not int or score < 0 for score in scores):
                raise ValueError("final weekly calendar requires observed final scores")
            final += 1
        elif any(score is not None for score in scores):
            raise ValueError("nonfinal weekly calendar cannot invent final scores")
        saved_status = "FINAL" if game["completed"] else "SCHEDULED"
        updated += (saved_status, game["away_score"], game["home_score"]) != (row["status"], *scores)
    if calendar.get("final_games") != final or calendar.get("scheduled_games") != statuses["SCHEDULED"]:
        raise ValueError("weekly calendar final/scheduled counts differ")
    if calendar.get("status_counts", dict(statuses)) != dict(statuses):
        raise ValueError("weekly calendar status ledger differs")
    if calendar.get("status_or_score_updated_games") != updated:
        raise ValueError("weekly calendar update count differs")


def validate_observed_contracts(data):
    """Source observations carry no inferred probability or executable claim."""
    snapshot = data.get("observed_contract_snapshot")
    rows = data.get("observed_contracts", [])
    if snapshot is None:
        if rows:
            raise ValueError("observed contract snapshot receipt required")
        return
    if snapshot.get("schema") != "public.nba.observed_contract_snapshot.v1":
        raise ValueError("observed contract snapshot schema required")
    if (snapshot.get("fixed_model_horizon_join_qualified") is not False
            or snapshot.get("source_observations_are_model_inputs") is not False
            or any(snapshot.get(key) != 0 for key in ("qualified_side_probabilities", "qualified_fees", "new_fits", "new_model_inference_calls"))):
        raise ValueError("source-only capture cannot qualify model probabilities or fees")
    if len(rows) != snapshot.get("observed_contract_count") or len({r["contract_id"] for r in rows}) != len(rows):
        raise ValueError("observed contract denominator or unique identity differs")
    games = {g["game_id"]: g for g in data["games"]}
    capture = parse_time(snapshot["captured_at_utc"])
    targets = Counter()
    for row in rows:
        game = games.get(row["game_id"])
        if not game or not game["in_week"]:
            raise ValueError("observed contract outside full week manifest")
        if (row.get("operator") != "gt" or row.get("period") != "FULL_GAME"
                or row.get("overtime_included") is not True
                or row.get("variable") not in {"away_margin", "home_margin", "total"}
                or not isinstance(row.get("proposition"), str) or not row["proposition"]):
            raise ValueError("exact supported contract proposition required")
        expected_kind = "total" if row["variable"] == "total" else "spread"
        if row.get("market_kind") != expected_kind or not isinstance(row.get("strike"), (int, float)):
            raise ValueError("contract target and strike orientation differ")
        targets[expected_kind] += 1
        if not parse_time(row["observed_at_utc"]) <= parse_time(row["retrieved_at_utc"]) <= capture:
            raise ValueError("observed quote clock outside capture")
        if parse_time(row["retrieved_at_utc"]) >= parse_time(game["tip_at_utc"]):
            raise ValueError("captured pregame quote is after game start")
        if (row.get("quote_status") != "CAPTURED_ASK_NOT_LIVE_EXECUTION_QUOTE"
                or row.get("quote_timestamp_utc") is not None
                or row.get("market_metadata_timestamp_is_quote_timestamp") is not False):
            raise ValueError("source capture cannot invent an exchange quote timestamp")
        if any(row.get(key) is not None for key in ("chosen_side", "chosen_side_probability", "p_yes", "p_no", "rank", "net_return_after_fees")):
            raise ValueError("observed source row cannot infer a model probability, side or return")
        for side in ("yes", "no"):
            price, quantity = row.get(side + "_ask"), row.get(side + "_ask_quantity")
            if price is not None and (not isinstance(price, (int, float)) or not 0 <= price <= 1):
                raise ValueError("captured ask must preserve a valid dollar price")
            if quantity is not None and (not isinstance(quantity, (int, float)) or quantity < 0):
                raise ValueError("captured ask quantity must remain unavailable or nonnegative")
    if targets != {"spread": snapshot["spread_count"], "total": snapshot["total_count"]}:
        raise ValueError("observed target denominators differ")
    if len({r["game_id"] for r in rows}) != snapshot["games_with_observed_contracts"]:
        raise ValueError("observed contract game coverage differs")
    for side in ("yes", "no"):
        if sum(r.get(side + "_ask_quantity") is not None for r in rows) != snapshot[side + "_ask_quantity_available"]:
            raise ValueError("observed ask quantity availability differs")


def validate(data):
    if data.get("schema") != "public.nba.spread_totals.v1":
        raise ValueError("sanitized NBA board schema required")
    if data.get("owner") != "NBA" or data.get("selection_uses_test_labels") is not False:
        raise ValueError("NBA-only, validation-selected evidence required")
    if data.get("source_refresh_performed_by_publication") is not False:
        raise ValueError("publishing cannot claim a source refresh")
    if data.get("production_model_deployment") != "NOT_PERFORMED":
        raise ValueError("this renderer cannot establish production model deployment")
    freshness = data.get("forecast_freshness")
    if freshness is not None:
        if (freshness.get("schema") != "public.nba.saved_forecast_freshness.v1"
                or freshness.get("status") != "STALE_SAVED_OUTLOOKS"
                or freshness.get("forecast_values_changed") is not False
                or freshness.get("model_inputs_refreshed") is not False
                or freshness.get("new_forecasts_issued") != 0
                or freshness.get("age_threshold_used") is not False):
            raise ValueError("saved forecast freshness cannot claim a new model issue")
        if parse_time(freshness["reviewed_at_utc"]).tzinfo is None:
            raise ValueError("forecast freshness review clock required")
    # No private execution identity, recipe, provider payload, or model state can
    # pass through the public projection even if accidentally nested in a row.
    forbidden = {
        "candidate_id", "selected_candidate_id", "model_id", "recipe_id",
        "feature_names", "feature_values", "feature_values_sha256",
        "blend_weights", "blend_member_ids", "model_pin", "source_reference",
        "bucket", "s3", "private_rows", "raw_body", "pmf", "support",
        "credentials", "secret", "api_key", "private_fit_reference",
    }

    def scan(value):
        if isinstance(value, dict):
            if forbidden.intersection(value):
                raise ValueError("private fields in public projection")
            for child in value.values():
                scan(child)
        elif isinstance(value, list):
            for child in value:
                scan(child)
        elif isinstance(value, str):
            if any(token in value for token in ("/home/", "s3://", "AKIA", "sagemaker-sports-edge-lab-")):
                raise ValueError("private path or credential marker in public projection")
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite public value")

    scan(data)
    games = data["games"]
    if len(games) != data["declared_games"]:
        raise ValueError("public game denominator differs from the observed manifest")
    if len({r["game_id"] for r in games}) != len(games):
        raise ValueError("duplicate observed game")
    if sum(r["completed"] for r in games) != data["completed_games"]:
        raise ValueError("completed game denominator differs")
    validate_week_calendar(data)
    validate_observed_contracts(data)
    for game in games:
        if game["season"] != "2026-27":
            raise ValueError("this public snapshot has one declared NBA season")
        tip = parse_time(game["tip_at_utc"])
        for horizon, roles in game["horizons"].items():
            if horizon not in {"60", "120"}:
                raise ValueError("unknown model horizon")
            if set(roles) != {"winner", "margin", "total"}:
                raise ValueError("every selected role must remain present, including gaps")
            for target, role in roles.items():
                value = role["value"]
                if value is None:
                    if not role.get("missing_reason"):
                        raise ValueError("missing value without named reason")
                    continue
                if not role.get("issued_at_utc") or parse_time(role["issued_at_utc"]) >= tip:
                    raise ValueError("no public forecast value without a saved pregame issue")
                if target == "winner" and not 0 <= value <= 1:
                    raise ValueError("probability out of bounds")
                if target == "total" and value < 0:
                    raise ValueError("negative expected total")
                if role.get("public_role_alias") is None or role.get("coarse_family") is None:
                    raise ValueError("public model role identity is required")
                if role.get("nominal_horizon_is_actual_issue_claim") is not False:
                    raise ValueError("nominal horizon cannot replace issue time")
    for role in data["roles"]:
        annual = role["annual"]
        if [a["season"] for a in annual] != ["2024-25", "2025-26", "2026-27"]:
            raise ValueError("annual populations required")
        obj = role["objective"]
        expected = .5 * annual[0]["metrics"][obj] + .5 * annual[1]["metrics"][obj]
        if not math.isclose(role["primary_score"], expected, abs_tol=1e-9):
            raise ValueError("primary score must use unchanged annual validation metrics")
    for contract in data.get("contracts", []):
        if contract.get("qualification") not in {"QUALIFIED", "UNPRICED"}:
            raise ValueError("blocked contract cannot publish a trading side")
        if contract.get("side") not in {"YES", "NO"}:
            raise ValueError("binary contract side required")
        if contract.get("complement_check") is not True or contract.get("orientation_check") is not True or contract.get("monotonicity_check") is not True:
            raise ValueError("contract probability checks must pass")
        if not math.isclose(contract["p_yes"] + contract["p_no"], 1, abs_tol=1e-8):
            raise ValueError("contract complements do not sum to one")
    return data


def render(data):
    validate(data)
    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    compact = compact.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    # The source template and generated page live at different depths. Keep
    # both real download links valid without changing the evidence contents.
    template = TEMPLATE.read_text().replace(
        'href="../../tracks/nba/current/board.json"', 'href="board.json"'
    )
    return template.replace("__BOARD_JSON__", compact)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    data = json.loads(args.data.read_text())
    html = render(data)
    public_json = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    expected = {"index.html": html, "board.json": public_json}
    if args.check:
        for name, content in expected.items():
            if not (args.output / name).is_file() or (args.output / name).read_text() != content:
                raise SystemExit(f"public NBA board differs: {name}")
        print("NBA board matches sanitized evidence; issue, denominator and privacy checks passed.")
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        for name, content in expected.items():
            (args.output / name).write_text(content)
        print(json.dumps({"games": len(data["games"]), "sha256": hashlib.sha256(html.encode()).hexdigest()}))


if __name__ == "__main__":
    main()
