"""Export every weekly FBS game and exact primary point baselines from checked public data."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
import io
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from build_board import validate


def pacific(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles")).strftime("%b %d %I:%M %p %Z") if value else "TBD"


def csv_text(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def markdown(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def export(data):
    validate(data)
    weekly = sorted((g for g in data["games"] if g["is_current_week"]), key=lambda g: (g.get("kickoff_utc") or "9999", g["game_id"]))
    primary = {(c["game_id"], c["market"]): c for c in data["contracts"] if c["primary_for_game"]}
    rows, contracts = [], []
    for g in weekly:
        p = g["winner"]["home_probability"]
        winner = None if p is None else g["home"] if p >= .5 else g["away"]
        win_p = None if p is None else max(p, 1 - p)
        margin = g["margin"]["home_minus_away"]
        favorite = None if margin is None else g["home"] if margin > 0 else g["away"] if margin < 0 else "Even point estimate"
        rows.append({"game_id": g["game_id"], "kickoff_utc": g["kickoff_utc"], "kickoff_pacific": pacific(g["kickoff_utc"]),
            "status": g["status"], "away": g["away"], "home": g["home"], "winner": winner,
            "winner_probability": None if win_p is None else round(win_p, 4), "winner_model": g["winner"]["model"],
            "winner_calibration": g["winner"]["calibration_status"], "margin_favorite": favorite,
            "margin_favorite_points": None if margin is None else abs(margin), "signed_home_minus_away": margin,
            "margin_model": g["margin"]["model"], "total_points": g["total"]["points"], "total_model": g["total"]["model"],
            "forecast_as_of": g["forecast_as_of"], "forecast_kind": g["forecast_kind"], "original_issued": g["original_issued"]})
        for market in ("spread", "total"):
            c = primary.get((g["game_id"], market)) or {}
            side = c.get("point_baseline_side")
            quote = c.get("sides", {}).get(side, {})
            contracts.append({"game_id": g["game_id"], "kickoff_pacific": pacific(g["kickoff_utc"]), "status": g["status"],
                "away": g["away"], "home": g["home"], "market": market, "contract_id": c.get("contract_id"),
                "exact_proposition": c.get("proposition"), "basis": c.get("basis"), "operator": c.get("operator"),
                "strike": c.get("strike"), "point_baseline_side": side, "point_center": c.get("point_baseline_value"),
                "model": c.get("point_baseline_model"), "binary_probability": None, "probability_rank": None,
                "forecast_as_of": g["forecast_as_of"], "contract_observed_at": c.get("observed_at"),
                "chosen_side_observed_ask": quote.get("observed_ask_price"), "ask_observed_at": quote.get("observed_ask_at"),
                "ask_status": quote.get("observed_ask_status"), "executable_price": quote.get("executable_price"),
                "settlement_status": c.get("settlement_status"), "equality_settles": c.get("equality_settles"),
                "qualification": "UNRANKED_POINT_BASELINE_NO_BINARY_PROBABILITY" if side else "POINT_BASELINE_UNAVAILABLE" if c else "NO_AUTHENTIC_OBSERVED_CONTRACT"})
    local_day = datetime.fromisoformat(data["clocks"]["forecast_as_of"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles")).date()
    start = local_day - timedelta(days=local_day.weekday())
    end = start + timedelta(days=6)
    header = [f"# FBS Spread & Totals — all {len(rows)} weekly games", "",
        f"Forecast snapshot: **{data['clocks']['forecast_as_of']}**. Week: {start.isoformat()} through {end.isoformat()} Pacific. "
        f"All **{len(rows)} games** remain visible; the full season board retains {len(data['games'])} observed games.", "",
        "Winner = P06, the saved six-family pre-test calibrated blend; expected margin = P02 CatBoost market control; total = P05 PyTorch market control. "
        "Winner and point favorite can differ because they come from different objective-selected models. "
        "These are early previews or completed-game reconstructions, not new original pregame issues. New research fits in this preparation: **0**.", "",
        "## Winner, signed margin and total", "",
        "| Pacific kickoff | Status | Away at home | Winner (P06) | Win probability | Point favorite (P02) | Home − away | Total (P05) |",
        "| --- | --- | --- | --- | ---: | --- | ---: | ---: |"]
    for r in rows:
        favorite = "Unavailable" if r["margin_favorite_points"] is None else f"{r['margin_favorite']} by {r['margin_favorite_points']:.1f}"
        values = [r["kickoff_pacific"], r["status"], r["away"] + " at " + r["home"], r["winner"] or "Unavailable",
                  "Unavailable" if r["winner_probability"] is None else f"{r['winner_probability']:.1%}", favorite,
                  "Unavailable" if r["signed_home_minus_away"] is None else f"{r['signed_home_minus_away']:+.1f}",
                  "Unavailable" if r["total_points"] is None else f"{r['total_points']:.1f}"]
        header.append("| " + " | ".join(map(markdown, values)) + " |")
    header += ["", "## Exact primary strikes — point baselines only", "",
        "YES/NO below are transparent comparisons of point estimates with observed contract thresholds. "
        "They have **no calibrated contract probability, probability rank or fee-adjusted return**. "
        "The native Kalshi capture is dated " + data["clocks"]["market_as_of"] + "; observed asks are stale in this board. "
        "The complete exact propositions, side-specific observed asks and settlement statuses are in the companion contract CSV and board alternatives. "
        "Normally resolved equality follows each actual strict/inclusive proposition; it is never a tie/push selection.", "",
        "| Away at home | Primary spread proposition / point side (P02) | Primary total proposition / point side (P05) |",
        "| --- | --- | --- |"]
    for g in weekly:
        labels = []
        for market in ("spread", "total"):
            c = primary.get((g["game_id"], market))
            if not c or not c.get("point_baseline_side"):
                labels.append("No authentic observed contract")
                continue
            basis = "Combined points" if c["basis"] == "total" else (g["home"] if c["basis"] == "home_margin" else g["away"]) + " margin"
            labels.append(f"{basis} {c['operator']} {c['strike']:g} → {c['point_baseline_side']} (point {c['point_baseline_value']:.1f})")
        header.append("| " + " | ".join(map(markdown, [g["away"] + " at " + g["home"], *labels])) + " |")
    header += ["", "All alternatives and missing inputs remain in [the complete board](index.html). "
        "The board's evidence tab separates original annual cards, current completed-game diagnostics, source coverage and publication status. "
        "The 70% contract-accuracy goal is a research target; straight-up winner accuracy does not establish that result.", ""]
    return {"weekly_games.csv": csv_text(rows), "weekly_contract_point_baselines.csv": csv_text(contracts), "weekly_games.md": "\n".join(header)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.data.read_text())
    results = export(data)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, text in results.items():
        destination = args.output / name
        if args.check:
            if not destination.exists() or destination.read_text() != text:
                raise ValueError("Weekly export differs: " + name)
        else:
            destination.write_text(text)
    print(json.dumps({"status": "PASS", "games": sum(g["is_current_week"] for g in data["games"]),
                      "files": list(results), "new_fits": 0, "new_probabilities": 0}))


if __name__ == "__main__":
    main()
