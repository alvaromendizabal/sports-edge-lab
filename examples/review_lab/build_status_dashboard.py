"""Generate the self-contained public dashboard from sanitized aggregates only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .fault_isolation import walkthrough
from .recoverable_stages import walkthrough as recovery_walkthrough
from .portable_recovery import walkthrough as portable_walkthrough
from .shared_inventory import walkthrough as shared_walkthrough
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/dashboard/index.html"


def payload():
    latest = json.loads((ROOT / "docs/evidence/2026-10-28-v132-execution.json").read_text())
    failed = json.loads((ROOT / "docs/evidence/2026-10-28-v131-execution.json").read_text())
    prior = json.loads((ROOT / "docs/evidence/2026-10-28-v129-execution.json").read_text())
    rows = []
    for row in latest["panels"]:
        rows.append({**row, "release": "V132"})
    for row in failed["historical_panels"]:
        rows.append({**row, "release": "V131", "mode": "HISTORICAL", "qualification": "REFERENCE_NOT_A_CHALLENGER" if row["model"] == "MARKET reference" else "INCOMPLETE"})
    for row in prior["annual_primary_comparisons"]:
        common = {"release": "V129", "mode": "HISTORICAL", "qualification": "FAILED", "league": "NFL" if row["league"] == "nfl" else "FBS",
                  "season": row["season_starting"], "games": row["n"], "policy": "annual",
                  "origin": "through_" + str(row["season_starting"] - 1), "correct": None, "incorrect": None, "ece10": None}
        rows.append({**common, "model": "Previous primary", "win_logloss": row["primary_log_loss"], "win_brier": row["primary_brier"], "delta_ci95": row["paired_logloss_ci95"]})
        rows.append({**common, "qualification": "REFERENCE_NOT_A_CHALLENGER", "model": "MARKET reference", "win_logloss": row["market_log_loss"], "win_brier": row["market_brier"], "delta_ci95": [0, 0]})
    for row in prior["monitoring"]:
        rows.append({"release": "V129", "mode": "MONITORING", "qualification": "NOT_FOR_SELECTION", "league": "NFL" if row["league"] == "nfl" else "FBS",
                     "season": 2026, "games": row["n"], "policy": "annual", "origin": "retained_monitoring_aggregate",
                     "model": "MARKET reference (primary identical)", "win_logloss": row["log_loss"], "win_brier": row["brier"],
                     "correct": row["correct"], "incorrect": row["incorrect"], "ece10": None})
    return {"completed_research": latest, "owner": json.loads((ROOT / "docs/evidence/2026-10-28-v134-execution.json").read_text()),
            "previous_owner": json.loads((ROOT / "docs/evidence/2026-10-28-v133-execution.json").read_text()), "shared_inventory": shared_walkthrough(),
            "rows": rows, "recovery": recovery_walkthrough(), "portability": portable_walkthrough(),
            "scenarios": {s: walkthrough(s) for s in ("research_failure", "research_complete", "stale_reference", "future_reference")}}


def render():
    data = json.dumps(payload(), sort_keys=True, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    template = (Path(__file__).with_name("dashboard.html.template")).read_text()
    return template.replace("__DASHBOARD_DATA__", data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != expected:
            raise SystemExit("Dashboard is stale; rebuild with python -m examples.review_lab.build_status_dashboard")
        print("Public dashboard matches sanitized evidence and executable synthetic scenarios")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(expected)
        print(OUTPUT.relative_to(ROOT))


if __name__ == "__main__": main()
