"""Render the NCAA B063 preservation dashboard from pinned public source bytes.

This report performs no model fitting, inference, source acquisition or promotion.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_COMMIT = "268d9db3752a93ed089821350c664ce3b9293653"
SOURCE_PINS = {
    "examples/ncaa_review/B062_STATUS.json": "94f0ac170f86ce68d4997a8c7245cd0464889f49",
    "examples/ncaa_review/B062_REPORT_DATA.json": "079b5565d63caa12ae66fe0ac7083d7f945b8ab8",
    "examples/ncaa_review/data/ncaa_observed_games_b060.json": "daaba167a4302667320762b1d3fd7f9040bbaefe",
    "examples/ncaa_review/data/ncaa_preserved_selected_issues_scored_b061.json": "f1574552fb3bd0086f375fde234e22373ce373c9",
}
GAME_COLUMNS = [
    "league", "event_id", "event_time", "home_team", "away_team", "completed",
    "actual_home_points", "actual_away_points", "source_binding_status",
    "forecast_status", "original_replay_prediction_status",
    "selected_original_home_win_probability", "selected_original_margin",
    "selected_original_total", "selected_issued_home_win_probability",
    "selected_issued_margin", "selected_issued_total", "time_precision",
    "tipoff_pacific", "provider_comparison_status",
]

def pinned_sources(root=ROOT):
    sources = {}
    for name, expected in SOURCE_PINS.items():
        raw = (root / name).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != expected:
            raise ValueError("B063 source identity mismatch: " + name)
        sources[name] = json.loads(raw)
    return sources

def validate(data, sources):
    status = sources["examples/ncaa_review/B062_STATUS.json"]
    report = sources["examples/ncaa_review/B062_REPORT_DATA.json"]
    census = sources["examples/ncaa_review/data/ncaa_observed_games_b060.json"]
    issued = sources["examples/ncaa_review/data/ncaa_preserved_selected_issues_scored_b061.json"]
    if data["source_commit"] != SOURCE_COMMIT:
        raise ValueError("B063 source commit")
    if {p["path"]: p["git_blob_sha"] for p in data["source_pins"]} != SOURCE_PINS:
        raise ValueError("B063 source pins")
    if data["game_columns"] != GAME_COLUMNS:
        raise ValueError("B063 game column identity")
    expected = [[r.get(k) for k in GAME_COLUMNS] for r in census["records"]]
    if data["games"] != expected:
        raise ValueError("B063 source records, values or order changed")
    for key in ("current_frozen_reference", "preserved_issues", "historical_leaders"):
        if data[key] != status[key]:
            raise ValueError("B063 saved scientific aggregate changed: " + key)
    if data["issued_archive"] != issued:
        raise ValueError("B063 original issue archive changed")
    if data["roles"] != report["preserved_selected_roles"] or data["market"] != report["market"]:
        raise ValueError("B063 saved roles or provider evidence changed")
    if (data["coverage"] != status["source_inventory"]
            or data["source_counts"] != census["counts"]
            or data["complete_official_universe"] is not False
            or data["evidence_asof_utc"] != status["evidence_asof_utc"]
            or data["census_asof_utc"] != census["asof"]):
        raise ValueError("B063 source clocks or denominator changed")
    execution = data["execution"]
    if (any(execution[k] != 0 for k in ("new_owner_fits", "new_issued_forecasts", "promotions"))
            or execution["parallelism_verified"] is not False
            or execution["status"] != "ENGINEERING_RECOVERY_IN_PROGRESS_OWNER_RUNTIME_PENDING"):
        raise ValueError("B063 publication cannot acquire owner science credit")
    if len(data["games"]) != 3457 or len(data["issued_archive"]["records"]) != 96:
        raise ValueError("B063 full preserved population")
    return data

def load_payload():
    raw = (HERE / "B063_PUBLIC_DATA.json").read_text()
    data = validate(json.loads(raw), pinned_sources())
    return data, raw.strip()

def render(legacy_html):
    _, raw = load_payload()
    start = legacy_html.index("<main>") + len("<main>")
    end = legacy_html.rindex("</main>")
    legacy_body = legacy_html[start:end]
    template = (HERE / "b063_dashboard.html.tmpl").read_text()
    from terminal_dashboard import render as render_terminal
    return render_terminal(template.replace("__B063_DATA__", raw.replace("<", "\\u003c")).replace("__B063_LEGACY__", legacy_body))

