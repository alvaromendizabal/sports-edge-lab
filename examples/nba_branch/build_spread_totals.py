"""Render the NBA board from an already sanitized public projection.

This module does not read private owner archives, fit models, collect prices, or
change source/issue clocks. Public role aliases are the only model identifiers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "tracks/nba/current/board.json"
TEMPLATE = Path(__file__).with_name("spread_totals_template.html")
OUTPUT = ROOT / "docs/nba/spread-totals"


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(data):
    if data.get("schema") != "public.nba.spread_totals.v1":
        raise ValueError("sanitized NBA board schema required")
    if data.get("owner") != "NBA" or data.get("selection_uses_test_labels") is not False:
        raise ValueError("NBA-only, validation-selected evidence required")
    if data.get("source_refresh_performed_by_publication") is not False:
        raise ValueError("publishing cannot claim a source refresh")
    if data.get("production_model_deployment") != "NOT_PERFORMED":
        raise ValueError("this renderer cannot establish production model deployment")
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
