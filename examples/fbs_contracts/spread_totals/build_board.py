"""Build the FBS Spread & Totals public board from an already-qualified export.

This presentation module does not fit, calibrate, price, settle or issue models.
It rejects unsupported public probabilities and keeps the full game manifest.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import html
import json
import math
from pathlib import Path
import re
from urllib.parse import urlparse

SCHEMA = "fbs.spread-totals.public-board.v1"
SIDES = {"YES", "NO"}
OPERATORS = {">", ">=", "<", "<="}
ROOT_KEYS = {"schema", "owner", "product", "release", "clocks", "selection",
             "population", "models", "games", "contracts", "missing_inputs",
             "performance", "publication", "provenance", "graphics", "source_coverage"}
GAME_KEYS = {"game_id", "home", "away", "kickoff_utc", "status", "is_current_week",
             "home_score", "away_score", "winner", "margin", "total", "forecast_kind",
             "forecast_as_of", "nominal_cutoff_utc", "forecast_horizon", "original_issued"}
CONTRACT_KEYS = {"contract_id", "game_id", "market", "source", "proposition", "strike", "operator",
                 "basis", "period", "terms_summary", "source_url", "terms_url", "equality_settles", "settlement_status",
                 "model", "forecast_as_of", "observed_at", "forecast_horizon", "probability_qualified",
                 "p_yes", "p_no", "integer_mass_preserved", "orientation_checked", "monotonicity_checked",
                 "comparable_group", "most_probable_side", "primary_for_game", "best_return_side", "sides",
                 "gap_reason", "point_baseline_side", "point_baseline_model", "point_baseline_value",
                 "point_baseline_comparison_checked"}
QUOTE_KEYS = {"executable_price", "executable_at_observation", "observed_at", "fee_per_contract",
              "fees_qualified", "expected_net_per_contract", "return_method", "gap_reason",
              "observed_ask_price", "observed_ask_at", "observed_ask_status"}
PRIVATE = re.compile(r"s3://|/home/sagemaker-user|/workspace/|AKIA[A-Z0-9]{16}|"
                     r"(?i:secret_access_key|access_token|api[_-]?key|authorization:)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def clock(value, name, optional=False):
    if value is None and optional:
        return None
    require(isinstance(value, str), f"{name}: clock required")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name}: invalid clock") from exc
    require(dt.tzinfo is not None, f"{name}: timezone required")
    return dt


def validate(data):
    require(isinstance(data, dict) and set(data) <= ROOT_KEYS, "unknown public root fields")
    require(data.get("schema") == SCHEMA and data.get("owner") == "fbs", "FBS schema required")
    require(data.get("product") == "Spread & Totals", "exact product name required")
    require(not PRIVATE.search(json.dumps(data, ensure_ascii=False)), "private material in export")
    for field in ("release", "clocks", "selection", "population", "models", "publication"):
        require(isinstance(data.get(field), dict), f"{field}: object required")
    for field in ("games", "contracts", "missing_inputs", "performance", "provenance"):
        require(isinstance(data.get(field), list), f"{field}: list required")
    for name in ("generated_at", "forecast_as_of"):
        clock(data["clocks"].get(name), name)
    clock(data["clocks"].get("market_as_of"), "market_as_of", optional=True)
    selection = data["selection"]
    require(selection.get("validation_seasons") == [2024, 2025], "validation years changed")
    require(selection.get("test_season") == 2026, "test year changed")
    require(selection.get("test_used_for_selection") is False, "test selection forbidden")
    require(selection.get("primary_weights") == [0.5, 0.5], "primary weights must be 50/50")
    require(selection.get("training_year_reweighting") is False, "training reweighting forbidden")
    require(isinstance(selection.get("primary_strike_rule"), str) and selection["primary_strike_rule"],
            "predeclared primary strike rule required")
    # A prepared campaign is release information, not authority to relabel the
    # inherited model forecasts or their original evaluation populations.
    next_research = data["release"].get("next_research")
    if next_research is not None:
        require(isinstance(next_research, dict), "next research object required")
        require(set(next_research) <= {"release", "status", "scope", "training_seasons", "selection_season",
                "selection_regime", "prior_test_exposure_disclosed", "prospective_test", "forecast_snapshot_replaced",
                "new_fits_reported", "new_calibrations_reported", "campaign_summary", "resource_policy",
                "incumbent_comparison", "calibration_protocol", "weather_campaign"}, "next research exceeds public status scope")
        require(next_research.get("status") == "PREPARED_AWAITING_OWNER_LAUNCH",
                "prepared research cannot claim executed results")
        require(next_research.get("scope") == ["margin", "total"], "next research must remain FBS spread and total scoped")
        require(next_research.get("training_seasons") == [2024, 2025]
                and next_research.get("selection_season") == 2026,
                "next research split must follow the explicit owner override")
        require(next_research.get("selection_regime") == "2026_EXPOSED_VALIDATION"
                and next_research.get("prior_test_exposure_disclosed") is True,
                "2026 selection must disclose prior exposure")
        require(next_research.get("forecast_snapshot_replaced") is False,
                "prepared campaign cannot replace inherited forecasts")
        require(next_research.get("new_fits_reported") == 0
                and next_research.get("new_calibrations_reported") == 0,
                "prepared campaign cannot credit unexecuted fits")
        require(bool(next_research.get("prospective_test")), "future test boundary must be disclosed")
        weather = next_research.get("weather_campaign")
        if weather is not None:
            require(isinstance(weather, dict) and set(weather) <= {
                "status", "registered_base_fit_jobs", "completed_base_fit_jobs",
                "new_calibration_fits", "forecast_rows_published", "source_summary",
                "roof_semantics", "comparison_scope"}, "weather preparation exceeds public scope")
            require(weather.get("status") == "REGISTERED_NOT_EXECUTED",
                    "prepared weather must remain unexecuted")
            require(type(weather.get("registered_base_fit_jobs")) is int
                    and weather["registered_base_fit_jobs"] > 0,
                    "weather registration needs a finite job count")
            require(all(type(weather.get(k)) is int and weather[k] == 0 for k in (
                "completed_base_fit_jobs", "new_calibration_fits", "forecast_rows_published")),
                    "prepared weather cannot claim fits or forecasts")
            require(all(isinstance(weather.get(k), str) and weather[k] for k in (
                "source_summary", "roof_semantics", "comparison_scope")),
                    "weather source, roof and comparison qualifications required")
    recovery = data["release"].get("recovery_audit")
    if recovery is not None:
        require(isinstance(recovery, dict), "recovery audit object required")
        counts = ("qualified_base_jobs", "source_blocked_base_jobs", "registered_base_jobs",
                  "saved_base_fit_states", "saved_calibration_components", "completed_prediction_partitions",
                  "saved_states_requiring_prediction_export", "unfinished_attempts_without_commit",
                  "remaining_base_fits_if_unchanged", "remaining_calibrations_if_unchanged")
        require(set(recovery) <= set(counts) | {"condition", "native_release_verified", "native_self_test_passed",
                "owner_run_launched_by_preparation", "scientific_callbacks_changed", "new_champions_selected", "fixes"},
                "recovery audit exceeds public status scope")
        require(all(type(recovery.get(k)) is int and recovery[k] >= 0 for k in counts),
                "recovery counts must be nonnegative integers")
        require(recovery["completed_prediction_partitions"] + recovery["saved_states_requiring_prediction_export"]
                == recovery["saved_base_fit_states"], "saved fits and prediction partitions disagree")
        require(recovery["saved_base_fit_states"] + recovery["remaining_base_fits_if_unchanged"]
                == recovery["qualified_base_jobs"], "remaining fit denominator disagrees")
        require(recovery["qualified_base_jobs"] + recovery["source_blocked_base_jobs"]
                == recovery["registered_base_jobs"], "blocked and qualified budgets disagree")
        require(recovery.get("condition") and recovery.get("owner_run_launched_by_preparation") is False
                and recovery.get("scientific_callbacks_changed") is False
                and recovery.get("new_champions_selected") is False,
                "prepared recovery cannot imply a new execution or champion")
        require(recovery.get("native_release_verified") is True and recovery.get("native_self_test_passed") is True,
                "native readiness requires verified executable and self-test")
    models = data["models"]
    for alias, model in models.items():
        require(re.fullmatch(r"[A-Z][0-9]{2}", alias) is not None, "public model aliases required")
        require(set(model) <= {"name", "family", "role", "calibration_status", "selection_objective"},
                "model export exceeds public scope")
    games = data["games"]
    require(len(games) == data["population"].get("manifest_games"), "full manifest denominator mismatch")
    ids = [g.get("game_id") for g in games]
    require(all(isinstance(i, str) and i for i in ids) and len(ids) == len(set(ids)), "game identity mismatch")
    by_id = dict(zip(ids, games))
    for g in games:
        require(set(g) <= GAME_KEYS, "game export exceeds public scope")
        require(isinstance(g.get("home"), str) and isinstance(g.get("away"), str), "team names required")
        clock(g.get("kickoff_utc"), "kickoff", optional=True)
        require(g.get("status") in {"scheduled", "completed", "postponed", "canceled", "unavailable"},
                "unknown game status")
        require(isinstance(g.get("is_current_week"), bool), "explicit current week membership required")
        for key, value_key in (("winner", "home_probability"), ("margin", "home_minus_away"), ("total", "points")):
            v = g.get(key)
            require(isinstance(v, dict) and v.get("model") in models, f"{key}: selected model required")
            require(set(v) <= {value_key, "model", "calibration_status", "gap_reason"},
                    "forecast export exceeds public scope")
            value = v.get(value_key)
            require(value is None or finite(value), f"{key}: invalid prediction")
            require(value is None or value != 0 or math.copysign(1.0, value) > 0,
                    "negative zero must be canonicalized at the public rounding boundary")
            require(value is not None or v.get("gap_reason"), f"{key}: missing input needs a reason")
            if key == "winner" and value is not None:
                require(0 <= value <= 1, "winner probability outside [0,1]")
                require(v.get("calibration_status") in {"fitted", "fitted_component_blend", "identity", "unknown"},
                        "winner calibration provenance required")
            if key == "total" and value is not None:
                require(value >= 0, "negative game total")
        require(isinstance(g.get("forecast_kind"), str) and g["forecast_kind"], "forecast provenance required")
        clock(g.get("forecast_as_of"), "game forecast clock", optional=True)
        require(isinstance(g.get("original_issued"), bool), "issuance label required")
    require(sum(g["is_current_week"] for g in games) == data["population"].get("current_week_games"),
            "current week denominator mismatch")
    coverage = data.get("source_coverage", [])
    require(isinstance(coverage, list), "source coverage must be a list")
    for row in coverage:
        require(set(row) <= {"provider", "bookmaker", "season", "target", "horizon", "observed_at",
                             "received_rows", "qualified_rows", "qualified_game_count", "manifest_games",
                             "weekly_game_count", "weekly_manifest_games", "gap_counts", "benchmark_status"},
                "source coverage exceeds public scope")
        require(row.get("provider") == "The Odds API" and isinstance(row.get("bookmaker"), str),
                "source provider and bookmaker identity required")
        require(row.get("season") == 2026 and row.get("target") in {"winner", "margin", "total"},
                "current source target scope changed")
        require(row.get("manifest_games") == len(games) and
                row.get("weekly_manifest_games") == data["population"]["current_week_games"],
                "source coverage denominator cannot shrink")
        for key in ("received_rows", "qualified_rows", "qualified_game_count", "weekly_game_count"):
            require(isinstance(row.get(key), int) and row[key] >= 0, "source count required")
        require(row["qualified_rows"] <= row["received_rows"] and
                row["qualified_game_count"] <= row["manifest_games"] and
                row["weekly_game_count"] <= row["weekly_manifest_games"], "invalid source coverage count")
        require(row.get("benchmark_status") == "CURRENT_REFERENCE_ONLY_NO_SCORED_COMPARISON",
                "current snapshot cannot establish a historical scored comparison")
        require(row.get("horizon") == "CURRENT_OBSERVATION_NOT_CANONICAL_T60", "source horizon relabeled")
        require(isinstance(row.get("gap_counts"), dict) and
                all(isinstance(v, int) and v >= 0 for v in row["gap_counts"].values()), "source gaps required")
        clock(row.get("observed_at"), "source coverage clock")
    for row in data["population"].get("external_status_ledger", []):
        require(row.get("official_status") == "canceled" and row.get("source_completed") is False and
                row.get("eligible_for_completed_game_grading") is False,
                "external canceled fixture cannot be graded as completed")
        require(isinstance(row.get("sources"), list) and row["sources"], "external status source required")
        for source in row["sources"]:
            parsed = urlparse(source.get("url", ""))
            require(parsed.scheme == "https" and parsed.hostname in {"appstatesports.com", "libertyflames.com"}
                    and not parsed.username and not parsed.password and not parsed.query,
                    "external official status URL required")
    contracts = data["contracts"]
    cids = [c.get("contract_id") for c in contracts]
    require(all(isinstance(cid, str) and cid for cid in cids) and len(cids) == len(set(cids)),
            "missing or duplicate contract identity")
    groups = defaultdict(list)
    primaries = defaultdict(int)
    for c in contracts:
        require(set(c) <= CONTRACT_KEYS, "contract export exceeds public scope")
        require(c.get("game_id") in by_id, "contract outside full manifest")
        require(c.get("market") in {"spread", "total"}, "unsupported contract market")
        require(c.get("source") == "Kalshi", "contract source must be explicit")
        require(c.get("operator") in OPERATORS and finite(c.get("strike")), "exact threshold required")
        require(c.get("basis") in {"home_margin", "away_margin", "total"}, "explicit contract orientation required")
        require((c["market"] == "total") == (c["basis"] == "total"), "market/orientation mismatch")
        require(isinstance(c.get("proposition"), str) and c["proposition"], "exact proposition required")
        require(isinstance(c.get("period"), str) and c["period"], "contract period required")
        require(isinstance(c.get("terms_summary"), str) and c["terms_summary"], "settlement terms required")
        for url in (c.get("source_url"), c.get("terms_url")):
            if not url:
                continue
            parsed = urlparse(url)
            require(parsed.scheme == "https" and (parsed.hostname == "kalshi.com" or (parsed.hostname or "").endswith(".kalshi.com"))
                    and not parsed.username and not parsed.password and not parsed.query,
                    "public contract URL required")
        require(c.get("equality_settles") == ("YES" if c["operator"] in {">=", "<="} else "NO"),
                "equality must follow actual contract wording")
        require(c.get("settlement_status") in {"pending", "YES", "NO", "canceled", "void", "fair_price", "unavailable"},
                "contract has exactly YES/NO normal outcomes")
        require(c.get("model") in models, "contract selected model alias required")
        clock(c.get("forecast_as_of"), "contract forecast clock", optional=True)
        clock(c.get("observed_at"), "contract source clock", optional=True)
        if c.get("probability_qualified"):
            yes, no = c.get("p_yes"), c.get("p_no")
            require(finite(yes) and finite(no) and 0 <= yes <= 1 and 0 <= no <= 1, "invalid binary probabilities")
            require(abs(yes + no - 1) <= 1e-10, "YES and NO must be complements")
            require(c.get("integer_mass_preserved") is True, "integer score mass qualification required")
            require(c.get("orientation_checked") is True and c.get("monotonicity_checked") is True,
                    "orientation and monotonicity qualification required")
            side = c.get("most_probable_side")
            require(side in SIDES, "only YES or NO may be selected")
            require((yes if side == "YES" else no) >= max(yes, no) - 1e-10, "selected probability is not maximal")
            require(isinstance(c.get("comparable_group"), str) and c["comparable_group"], "comparable strike group required")
            groups[(c["game_id"], c["market"], c["basis"], c["operator"], c["period"],
                    c["model"], c["forecast_as_of"], c["comparable_group"])].append(c)
        else:
            require(c.get("p_yes") is None and c.get("p_no") is None, "unqualified probability cannot be published")
            require(c.get("most_probable_side") is None and c.get("gap_reason"), "missing probability needs explicit gap")
        baseline = c.get("point_baseline_side")
        if baseline is not None:
            require(baseline in SIDES and c.get("point_baseline_model") in models,
                    "point baseline must identify a YES/NO side and model")
            value = c.get("point_baseline_value")
            require(finite(value) and c.get("point_baseline_comparison_checked") is True,
                    "point baseline lacks checked oriented value")
            strike = c["strike"]
            yes = {">": value > strike, ">=": value >= strike,
                   "<": value < strike, "<=": value <= strike}[c["operator"]]
            require(baseline == ("YES" if yes else "NO"), "point baseline violates exact threshold")
        require(isinstance(c.get("primary_for_game"), bool), "primary strike flag required")
        if c["primary_for_game"]:
            primaries[(c["game_id"], c["market"])] += 1
        quotes = c.get("sides", {})
        require(isinstance(quotes, dict), "contract sides must be an object")
        require(set(quotes) <= SIDES, "third trading side forbidden")
        net = {}
        for side, q in quotes.items():
            require(isinstance(q, dict), "quote must be an object")
            require(set(q) <= QUOTE_KEYS, "quote export exceeds public scope")
            observed_price = q.get("observed_ask_price")
            require(observed_price is None or finite(observed_price) and 0 < observed_price < 1,
                    "invalid dated observed ask")
            if observed_price is not None:
                clock(q.get("observed_ask_at"), "dated ask clock")
                require(q.get("observed_ask_status") in {"STALE", "CURRENT", "CLOSED", "UNQUALIFIED"},
                        "dated ask qualification required")
            price = q.get("executable_price")
            require(price is None or finite(price) and 0 < price < 1, "invalid executable price")
            if price is not None:
                require(q.get("executable_at_observation") is True, "display price lacks executability proof")
                require(q.get("observed_ask_status") not in {"STALE", "CLOSED", "UNQUALIFIED"},
                        "stale or closed ask cannot become executable")
                clock(q.get("observed_at"), "executable quote clock")
            value = q.get("expected_net_per_contract")
            if value is not None:
                require(c.get("probability_qualified") and price is not None and finite(value), "net return lacks price/probability")
                require(q.get("fees_qualified") is True and finite(q.get("fee_per_contract")), "net return lacks fees")
                require(q["fee_per_contract"] >= 0, "negative transaction fee")
                require(q.get("return_method"), "net return convention required")
                probability = c["p_yes"] if side == "YES" else c["p_no"]
                require(abs(value - (probability - price - q["fee_per_contract"])) <= 1e-9,
                        "net return disagrees with one-dollar payout, price and fee")
                net[side] = value
        best = c.get("best_return_side")
        require(best is None or best in net, "best return side is not qualified")
        if best is not None:
            require(net[best] >= max(net.values()) - 1e-10, "best return side is not maximal")
    require(all(n <= 1 for n in primaries.values()), "multiple primary strikes in one game/market")
    for key, group in groups.items():
        ordered = sorted(group, key=lambda c: c["strike"])
        for a, b in zip(ordered, ordered[1:]):
            if a["strike"] == b["strike"]:
                require(abs(a["p_yes"] - b["p_yes"]) <= 1e-10, "same comparable strike has conflicting probability")
            elif key[3] in {">", ">="}:
                require(a["p_yes"] + 1e-10 >= b["p_yes"], "tail probability increases with strike")
            else:
                require(a["p_yes"] <= b["p_yes"] + 1e-10, "lower-tail probability decreases with strike")
    for gap in data["missing_inputs"]:
        require(gap.get("game_id") in by_id and gap.get("code") and gap.get("detail"), "missing-input ledger malformed")
    return data


def probability_rank(data, market, weekly=True):
    games = {g["game_id"]: g for g in data["games"]}
    rows = [c for c in data["contracts"] if c["market"] == market and c["primary_for_game"]
            and c.get("probability_qualified") and c["settlement_status"] == "pending"
            and (not weekly or games[c["game_id"]]["is_current_week"])]
    return sorted(rows, key=lambda c: (-max(c["p_yes"], c["p_no"]), games[c["game_id"]].get("kickoff_utc") or "", c["contract_id"]))


def return_rank(data, market, weekly=True):
    rows = [c for c in probability_rank(data, market, weekly) if c.get("best_return_side")]
    return sorted(rows, key=lambda c: (-c["sides"][c["best_return_side"]]["expected_net_per_contract"], c["contract_id"]))


def point_baseline_rows(data, market, weekly=True):
    """Chronological rows; these are expressly not probability-ranked picks."""
    games = {g["game_id"]: g for g in data["games"]}
    rows = [c for c in data["contracts"] if c["market"] == market and c["primary_for_game"]
            and c.get("point_baseline_side") in SIDES and c["settlement_status"] == "pending"
            and (not weekly or games[c["game_id"]]["is_current_week"])]
    return sorted(rows, key=lambda c: (games[c["game_id"]].get("kickoff_utc") or "9999", c["contract_id"]))


def build(data, template_path=None):
    validate(data)
    template_path = Path(template_path) if template_path else Path(__file__).with_name("board.html.in")
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode()).hexdigest()
    safe = payload.replace("<", "\\u003c").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return template_path.read_text().replace("@@BOARD_JSON@@", safe).replace("@@DATA_SHA256@@", digest).replace(
        "@@AS_OF@@", html.escape(data["clocks"]["forecast_as_of"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = json.loads(args.data.read_text())
    rendered = build(data)
    output = args.output or args.data.with_name("index.html")
    if args.check:
        require(output.read_text() == rendered, "generated board differs from qualified data")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered)
    print(json.dumps({"status": "PASS", "games": len(data["games"]), "contracts": len(data["contracts"]),
                      "weekly_spread_ranked": len(probability_rank(data, "spread")),
                      "weekly_total_ranked": len(probability_rank(data, "total")),
                      "new_fits": 0, "new_probabilities": 0}))


if __name__ == "__main__":
    main()
