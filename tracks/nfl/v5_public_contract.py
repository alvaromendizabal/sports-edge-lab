"""Public, bounded V5 reporting validation; contains no active model recipe."""
from __future__ import annotations
import math

OWNER_FIELDS = set("cycle status run_id return_bytes return_sha256 started_at finished_at first_error_at failure_class new_fits new_forecasts completed_research_stages latest_scientific_cycle retained_scientific_native_states retained_scientific_issue_rows independent_terminal_stdout_available qualification".split())
V5_FIELDS = set("status prepared_cycle actual_new_fits actual_new_forecasts automatic_promotion candidate_counts comparison_lanes evaluation_exposure full_history_role refresh_policy selection_policy missingness_policy metric_policy support_status verification".split())
COMPARISON_FIELDS = set("lane target purpose status eligible_games evaluated_games accuracy log_loss brier mae rmse crps support_requirement comparison_population absence_reason promotion_status".split())
EXPOSURE_FIELDS = set("evidence_class clock_rule evaluation_status selection_use".split())
LANES = {"Market-free foundation","Current-regime specialist","Online gated blend","Market-only control","Market residual challenger"}
EXPOSURES = {"Original frozen issued","Historical rolling reconstruction","Genuinely future issued rolling","Source-only reference"}

def validate_additions(data, only, instant):
    owner = data["n060_owner_status"]
    only(owner,OWNER_FIELDS,"N060 owner status")
    if (owner["cycle"],owner["status"],owner["latest_scientific_cycle"]) != ("N059","FAILED_BEFORE_RESEARCH_STAGES","N058"):
        raise ValueError("Actual failed owner state must remain separate from scientific state")
    if any(owner[k] != 0 for k in ("new_fits","new_forecasts","completed_research_stages")):
        raise ValueError("No scientific work credited to pre-stage failure")
    if owner["return_bytes"] != 971406 or owner["return_sha256"] != "d7c71d64b4944b455441ed54953dcbe788def3e897282554aeca47c6ef927c91":
        raise ValueError("Exact owner return identity")
    if not instant(owner["started_at"]) < instant(owner["first_error_at"]) <= instant(owner["finished_at"]):
        raise ValueError("Actual failure clocks")
    v5 = data["v5_scope"]
    only(v5,V5_FIELDS,"V5 scope")
    current = data.get("publication_cycle") == "N061"
    expected_status = "N060_OWNER_FAILED_N061_PREPARED" if current else "PREPARED_NOT_OWNER_EXECUTED"
    expected_cycle = "N061" if current else "N060"
    expected_row_status = "N060_OWNER_V5_FAILED_N061_REPAIR_PREPARED" if current else "PREPARED_NOT_OWNER_EXECUTED"
    if v5["status"] != expected_status or v5["prepared_cycle"] != expected_cycle or v5["automatic_promotion"]:
        raise ValueError("Prepared V5 cannot be relabeled as owner execution")
    if v5["actual_new_fits"] or v5["actual_new_forecasts"]:
        raise ValueError("Prepared V5 cannot create real science")
    rows = v5["comparison_lanes"]
    if len(rows) != 15 or {(r["lane"],r["target"]) for r in rows} != {(lane,target) for lane in LANES for target in ("win","margin","total")}:
        raise ValueError("Every prepared comparison lane and target must remain visible")
    for row in rows:
        only(row,COMPARISON_FIELDS,"V5 comparison")
        if row["status"] != expected_row_status or row["evaluated_games"] != 0 or row["eligible_games"] is not None:
            raise ValueError("V5 evaluated population requires actual execution")
        if any(row[k] is not None for k in ("accuracy","log_loss","brier","mae","rmse","crps")):
            raise ValueError("No synthetic, substituted or invented V5 proper score")
        if not row["absence_reason"] or row["promotion_status"] != "SHADOW_RESEARCH_PENDING_FORWARD_EVIDENCE":
            raise ValueError("Explicit comparison blocker and shadow status required")
    exposures = v5["evaluation_exposure"]
    if len(exposures) != 4 or {r["evidence_class"] for r in exposures} != EXPOSURES:
        raise ValueError("Four immutable exposure classes required")
    for row in exposures:
        only(row,EXPOSURE_FIELDS,"evaluation exposure")
        if not all(isinstance(row[k],str) and row[k] for k in EXPOSURE_FIELDS):
            raise ValueError("Exposure and chronology may not be omitted")
    counts = v5["candidate_counts"]
    allowed_counts = set("inherited_proposed inherited_implemented inherited_blocked new_proposed new_implemented new_blocked owner_materialized owner_admitted owner_evaluated owner_promoted".split())
    only(counts,allowed_counts,"feature counts")
    if set(counts) != allowed_counts or any(type(v) is not int or v < 0 for v in counts.values()):
        raise ValueError("Feature preparation and owner execution require distinct nonnegative counts")
    if counts["inherited_proposed"] != counts["inherited_implemented"] + counts["inherited_blocked"] or counts["new_proposed"] != counts["new_implemented"] + counts["new_blocked"]:
        raise ValueError("Prepared feature counts do not reconcile")
    if any(counts[k] for k in ("owner_materialized","owner_admitted","owner_evaluated","owner_promoted")):
        raise ValueError("Local synthetic verification cannot admit NFL features")
    for key in ("support_status","verification"):
        if not isinstance(v5[key],list) or not all(isinstance(v,str) and v for v in v5[key]):
            raise ValueError("Public V5 details require a bounded prose list")
    return data
