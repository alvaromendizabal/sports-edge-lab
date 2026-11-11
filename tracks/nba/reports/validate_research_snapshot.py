"""Validate a public NBA research snapshot; contains no model implementation."""
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import sys

def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timezone is required")
    return parsed

def validate_public_report(data):
    if data.get("schema") != "sports-edge-lab-nba-public-selected-research-outputs-v2":
        raise ValueError("Unexpected schema")
    games, roles, issues, views = (data[k] for k in ("games", "champions", "issues", "role_views"))
    asof = timestamp(data["evidence_as_of_utc"])
    seen = set()
    for key, issue in issues.items():
        encoded = json.dumps(issue, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        if hashlib.sha256(encoded).hexdigest()[:24] != key:
            raise ValueError("Public issue reference does not match its body")
        source, issued, start = (timestamp(issue[k]) for k in ("source_asof_utc", "issued_at_utc", "scheduled_start_at_issue_utc"))
        if not source <= issued < start or issued > asof:
            raise ValueError("Original source/pregame clock violation")
        if issue["target"] == "winner" and not 0 <= issue["prediction"] <= 1:
            raise ValueError("Invalid probability")
        if "prediction_intervals" in issue:
            if issue["target"] not in ("margin", "total") or not isinstance(issue["prediction_intervals"], dict) or not issue["prediction_intervals"]:
                raise ValueError("Invalid issued interval target/body")
            for level, bounds in issue["prediction_intervals"].items():
                if not re.fullmatch(r"[1-9][0-9]?", level) or not isinstance(bounds, list) or len(bounds) != 2:
                    raise ValueError("Invalid issued interval coverage/bounds")
                if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in bounds) or bounds[0] > bounds[1]:
                    raise ValueError("Invalid issued interval endpoints")
    for row in views:
        if row["game_id"] not in games or row["champion_role"] not in roles:
            raise ValueError("Unknown game or champion role")
        identity = (row["game_id"], row["champion_role"])
        if identity in seen:
            raise ValueError("Duplicate game/role view")
        seen.add(identity)
        role = roles[row["champion_role"]]
        if games[row["game_id"]]["phase"] != role["phase"]:
            raise ValueError("Game and role phase differ")
        for name in ("current_issue_ref", "at_issue_ref"):
            reference = row[name]
            if reference is not None:
                issue = issues[reference]
                if issue["game_id"] != row["game_id"] or issue["target"] != role["target"] or issue["horizon_minutes"] != role["horizon_minutes"]:
                    raise ValueError("Issue game/target/horizon differs from role")
        expected = "AVAILABLE_ORIGINAL_ISSUE" if row["current_issue_ref"] else "NO_ORIGINAL_ISSUE_FOR_CURRENT_CHAMPION"
        if row["current_forecast_status"] != expected:
            raise ValueError("Missing forecast status is inconsistent")
        if row["at_issue_ref"] is None and row["at_issue_matches_current_champion"] is not None:
            raise ValueError("Absent at-issue forecast has a match flag")
    expected = {(gid, key) for gid, game in games.items() for key, role in roles.items() if game["phase"] == role["phase"]}
    if seen != expected:
        raise ValueError("Game/role denominator is incomplete")
    checks = {"distinct_observed_games": len(games), "active_research_champion_roles": len(roles),
        "distinct_public_selected_issues": len(issues), "selected_champion_role_views": len(views),
        "distinct_public_selected_issues_with_intervals": sum("prediction_intervals" in issue for issue in issues.values()),
        "current_champion_forecast_available_views": sum(r["current_issue_ref"] is not None for r in views),
        "current_champion_forecast_missing_views": sum(r["current_issue_ref"] is None for r in views)}
    if any(data["coverage"][key] != value for key, value in checks.items()):
        raise ValueError("Coverage count differs from actual records")
    if data.get("current_outcome_selection") is not False or data.get("live_refresh") is not False:
        raise ValueError("This snapshot must explicitly retain its non-live research status")
    return checks

if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("latest_research_outputs.json")
    body = path.read_bytes()
    print(json.dumps({"status": "PASS", "sha256": hashlib.sha256(body).hexdigest(), **validate_public_report(json.loads(body))}, sort_keys=True))
