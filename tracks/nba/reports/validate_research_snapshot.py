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


import collections

_validate_original_projection = validate_public_report

def validate_public_report(data):
    if data.get("schema") != "sports-edge-lab-nba-public-schedule-complete-research-outputs-v3":
        raise ValueError("Unexpected complete-schedule schema")
    games, champions, issues = data["games"], data["champions"], data["issues"]
    original_ids = data["forecast_inventory_game_ids"]
    if len(original_ids) != len(set(original_ids)) or not set(original_ids) <= set(games):
        raise ValueError("Original issue game inventory changed")
    previous = dict(data)
    previous["schema"] = "sports-edge-lab-nba-public-selected-research-outputs-v2"
    previous["games"] = {key: games[key] for key in original_ids}
    previous["coverage"] = dict(data["coverage"], distinct_observed_games=len(original_ids))
    _validate_original_projection(previous)
    asof = timestamp(data["evidence_as_of_utc"])
    observation = data["schedule_observation"]
    if timestamp(observation["snapshot_finished_at_utc"]) > asof or observation["future_full_schedule_complete"] is not False:
        raise ValueError("Schedule clock or future-completeness claim invalid")
    expected_groups = {phase: sorted(key for key, role in champions.items() if role["phase"] == phase)
                       for phase in ("regular", "postseason")}
    expected_groups["none"] = []
    if data["role_groups"] != expected_groups:
        raise ValueError("Role group changed")
    coverage = data["game_coverage"]
    if set(coverage) != set(games):
        raise ValueError("Official game coverage denominator incomplete")
    views = {(row["game_id"], row["champion_role"]): row for row in data["role_views"]}
    target_keys = {f"{target}_T{horizon}" for target in ("winner", "margin", "total") for horizon in (60,120)}
    opportunities = available = 0
    for gid, game in games.items():
        if not re.fullmatch(r"[0-9]{1,20}", gid):
            raise ValueError("Invalid public game identifier")
        if game["schedule_membership"] == "CANONICAL_OFFICIAL":
            if timestamp(game["schedule_source_asof_utc"]) > timestamp(observation["snapshot_finished_at_utc"]):
                raise ValueError("Individual source clock exceeds snapshot")
            if game["source_status"] == "FINAL" and game["source_status_group"] != "COMPLETED_AS_OBSERVED":
                raise ValueError("Observed final status changed")
            if game["source_status"] != "FINAL" and game["source_status_group"] == "COMPLETED_AS_OBSERVED":
                raise ValueError("Time passage fabricated a final status")
            expected_status_group = "COMPLETED_AS_OBSERVED" if game["source_status"] == "FINAL" else "SCHEDULED_AS_OBSERVED" if game["source_status"] == "SCHEDULED" else "UNRESOLVED_AS_OBSERVED" if game["source_status"] == "TBD" else game["source_status"]
            if game["source_status_group"] != expected_status_group or game["official_status_at_source"] != game["source_status"]:
                raise ValueError("Official observed status changed")
        expected_identity = "RESOLVED_MATCHUP" if game["home_team"] and game["away_team"] else "UNRESOLVED_OFFICIAL_MATCHUP"
        if game["identity_status"] != expected_identity:
            raise ValueError("Matchup identity status changed")
        tip = game["scheduled_start_utc"]
        expected_time = "TIP_UNKNOWN" if tip is None else "FUTURE_TIP" if timestamp(tip) > asof else "START_TIME_PASSED_STATUS_NOT_INFERRED"
        if game["tip_time_relation_at_report"] != expected_time:
            raise ValueError("Game time relation inconsistent")
        row = coverage[gid]
        group = game["phase"] if game["phase"] in expected_groups else "none"
        aliases = expected_groups[group]
        if row["applicable_role_group"] != group:
            raise ValueError("Game applicable phase group changed")
        current = [alias for alias in aliases if views.get((gid, alias), {}).get("current_issue_ref")]
        at_issue = [alias for alias in aliases if views.get((gid, alias), {}).get("at_issue_ref")]
        missing = sorted(set(aliases) - set(current))
        missing_repr = "ALL_APPLICABLE_ROLES" if missing and len(missing) == len(aliases) else missing
        if (row["current_role_ids_available"] != current or row["at_issue_role_ids_available"] != at_issue
                or row["current_role_ids_missing"] != missing_repr):
            raise ValueError("Missing or available role denominator changed")
        if set(row["target_horizon"]) != target_keys:
            raise ValueError("Game target/horizon denominator incomplete")
        for key, cell in row["target_horizon"].items():
            target, horizon = key.rsplit("_T",1)
            matched = [alias for alias in aliases if champions[alias]["target"] == target and champions[alias]["horizon_minutes"] == int(horizon)]
            nc, na = len(set(matched) & set(current)), len(set(matched) & set(at_issue))
            if (cell["expected_roles"],cell["current_roles_available"],cell["at_issue_roles_available"]) != (len(matched),nc,na):
                raise ValueError("Target/horizon role counts inconsistent")
            if cell["status"] not in data["gap_reason_definitions"]:
                raise ValueError("Unknown gap reason")
            if cell["status"] == "AVAILABLE_ORIGINAL_ISSUES" and (not matched or nc != len(matched)):
                raise ValueError("Unissued target marked available")
            expected_reason = "AVAILABLE_ORIGINAL_ISSUES" if matched and nc == len(matched) else \
                "OFFICIAL_MATCHUP_NOT_ASSIGNED" if game["identity_status"] != "RESOLVED_MATCHUP" else \
                "OFFICIAL_PHASE_NOT_ADMITTED_TO_REGISTERED_MODEL_TARGETS" if game["phase"] not in ("regular","postseason") else \
                "NO_ACTIVE_CHAMPION_FOR_TARGET_HORIZON" if not matched else \
                "SOME_CURRENT_ROLE_ISSUES_MISSING" if nc else \
                "NO_ORIGINAL_ISSUE_FOR_CURRENT_CHAMPION" if na else \
                "OFFICIAL_TARGET_NOT_ADMITTED_AT_SOURCE" if game.get("target_registry_member_at_source") is False else \
                "NO_RECOVERED_ORIGINAL_PREGAME_FORECAST"
            if cell["status"] != expected_reason:
                raise ValueError("Gap reason differs from exact available role evidence")
        opportunities += len(aliases)
        available += len(current)
    official = {gid: game for gid, game in games.items() if game["schedule_membership"] == "CANONICAL_OFFICIAL"}
    regular = [game for game in official.values() if game["phase"] == "regular"]
    if observation["regular_season_observed_count"] != len(regular):
        raise ValueError("Regular-season denominator changed")
    expected_full = observation["regular_season_expected_full_count"]
    if expected_full is not None and observation["regular_season_not_observed_count"] != max(0,expected_full-len(regular)):
        raise ValueError("Unobserved regular-season slots changed")
    checks = {
        "distinct_observed_games": len(games), "games_in_original_issued_inventory": len(original_ids),
        "official_schedule_games": len(official), "official_games_without_original_issues": len(set(official)-set(original_ids)),
        "official_games_by_saved_status":dict(sorted(collections.Counter(g["source_status"] for g in official.values()).items())),
        "official_games_by_phase":dict(sorted(collections.Counter(g["phase"] for g in official.values()).items())),
        "official_resolved_matchups":sum(g["identity_status"]=="RESOLVED_MATCHUP" for g in official.values()),
        "official_unresolved_matchups":sum(g["identity_status"]!="RESOLVED_MATCHUP" for g in official.values()),
        "official_future_tips_at_report":sum(g["tip_time_relation_at_report"]=="FUTURE_TIP" for g in official.values()),
        "official_scheduled_start_passed_without_final_observation":sum(g["source_status"]=="SCHEDULED" and g["tip_time_relation_at_report"]=="START_TIME_PASSED_STATUS_NOT_INFERRED" for g in official.values()),
        "original_issue_games_absent_from_official_inventory": len(set(original_ids)-set(official)),
        "separate_secondary_observations": len(data["secondary_schedule_observations"]),
        "all_game_target_horizon_cells": len(games)*6,
        "all_game_applicable_role_opportunities": opportunities,
        "all_game_current_role_forecasts_available": available,
        "all_game_current_role_forecasts_missing": opportunities-available,
    }
    if any(data["coverage"][key] != value for key,value in checks.items()):
        raise ValueError("Complete-schedule coverage count differs from actual records")
    encoded = json.dumps(data,sort_keys=True)
    for field in ('"recipe_id"','"feature_names"','"calibration"','"source_snapshot_pin"','"engine_journal_pin"','"training_cutoff_utc"','"prediction_distribution"','"weights"','"sigmas"','"means"','/home/sagemaker-user','s3://','AKIA','AWS_SECRET_ACCESS_KEY'):
        if field in encoded:
            raise ValueError("Private field or path in public snapshot")
    return checks


_validate_schedule_projection=validate_public_report

def validate_public_report(data):
    if data.get('schema')!='sports-edge-lab-nba-public-source-separated-research-outputs-v4':
        raise ValueError('Unexpected source-separated schema')
    base=dict(data);base['schema']='sports-edge-lab-nba-public-schedule-complete-research-outputs-v3'
    checks=_validate_schedule_projection(base);asof=timestamp(data['evidence_as_of_utc'])
    result_fields={'status','home_points','away_points','ended_at_utc','observed_at_utc','available_at_utc',
        'published_at_utc','owner_release','evidence_track','original_historical_possession_claim','new_score_calculation'}
    attached=[];new_finals=[]
    for gid,game in data['games'].items():
        result=game.get('result_observation')
        if result:
            if set(result)!=result_fields or result['status']!='FINAL':raise ValueError('Result field allowlist changed')
            if result['original_historical_possession_claim'] is not False or result['new_score_calculation'] is not False:
                raise ValueError('Result evidence scope changed')
            if any(type(result[k]) is not int or result[k]<0 for k in ('home_points','away_points')):
                raise ValueError('Invalid saved final score')
            if (not timestamp(result['observed_at_utc'])<=timestamp(result['available_at_utc'])<=asof or
                    result['ended_at_utc'] is not None and timestamp(result['ended_at_utc'])>timestamp(result['observed_at_utc'])):
                raise ValueError('Saved result information clock changed')
            attached.append(gid)
            if game['source_status']!='FINAL':new_finals.append(gid)
        expected_status=result['status'] if result else game['source_status']
        expected_source='SAVED_RESULT_OBSERVATION' if result else 'SAVED_SCHEDULE_OBSERVATION'
        expected_clock=result['observed_at_utc'] if result else game['schedule_source_asof_utc']
        if (game['last_confirmed_status'],game['last_confirmed_status_source'],game['last_confirmed_status_asof_utc'])!=(expected_status,expected_source,expected_clock):
            raise ValueError('Latest status is not supported by its row')
    official={gid:g for gid,g in data['games'].items() if g['schedule_membership']=='CANONICAL_OFFICIAL'}
    row_counts=dict(sorted(collections.Counter(g['last_confirmed_status'] for g in official.values()).items()))
    if data['coverage']['official_games_by_latest_row_backed_status']!=row_counts:
        raise ValueError('Latest row-backed status denominator changed')
    recovery=data['result_observation_recovery'];aggregate=recovery.get('source_reported_status_counts')
    differences={key:{'row_backed':row_counts.get(key,0),'source_aggregate':aggregate.get(key,0)}
        for key in sorted(set(row_counts)|set(aggregate or {})) if aggregate is not None and row_counts.get(key,0)!=aggregate.get(key,0)}
    if data['coverage']['latest_row_and_source_aggregate_difference']!=differences:
        raise ValueError('Aggregate-only status discrepancy hidden')
    if recovery['status']!='NO_SEPARATE_RESULT_OVERLAY_SUPPLIED':
        if recovery['result_rows_attached']!=len(attached) or recovery['newly_confirmed_final_game_ids']!=sorted(new_finals):
            raise ValueError('Result overlay row denominator changed')
        if (recovery['full_B074_schedule_projection_reconstructed'] is not False or
                recovery['source_clock_rewritten'] is not False or recovery['original_forecast_values_or_clocks_changed'] is not False):
            raise ValueError('Result overlay misrepresents source or original forecasts')
        if aggregate is not None and sum(aggregate.values())!=recovery['source_reported_official_games']:
            raise ValueError('Saved aggregate denominator changed')
    return dict(checks,latest_row_backed_status_counts=row_counts)

if __name__=='__main__':
    from restore_snapshot_assets import restore
    restore()
    path=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('latest_research_outputs.json')
    body=path.read_bytes()
    print(json.dumps({'status':'PASS','sha256':hashlib.sha256(body).hexdigest(),**validate_public_report(json.loads(body))},sort_keys=True))
