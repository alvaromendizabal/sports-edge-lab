"""Public, invented-data demonstration of selection/serving/ledger identity.

This checks identity and chronology, not predictive quality or trade eligibility.
The production implementation and individual football forecasts remain private.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[2] / "docs/evidence/2026-10-27-v126-execution.json"


def digest(value: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("invalid SHA-256 identity")
    return value


def instant(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("clock must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid clock") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("clock requires an explicit timezone")
    return parsed.astimezone(timezone.utc)


def count(value: int) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative integer")
    return value


@dataclass(frozen=True)
class PolicyIdentity:
    league: str
    policy_id: str
    rule_sha256: str
    policy_kind: str
    learned_policy_qualified: bool

    def validate(self) -> None:
        if self.league not in ("nfl", "ncaaf") or not isinstance(self.policy_id, str) or not self.policy_id:
            raise ValueError("unknown league or empty policy identifier")
        digest(self.rule_sha256)
        if self.policy_kind not in ("market_fallback", "learned"):
            raise ValueError("unknown policy kind")
        if type(self.learned_policy_qualified) is not bool:
            raise ValueError("qualification must be explicit")
        if self.policy_kind == "learned" and not self.learned_policy_qualified:
            raise ValueError("unqualified learned policy")
        if self.policy_kind == "market_fallback" and self.learned_policy_qualified:
            raise ValueError("market reference is not a qualified learned policy")


@dataclass(frozen=True)
class Selection:
    sha256: str
    available_at: str
    seasons: tuple[int, ...]
    identities: tuple[PolicyIdentity, ...]


@dataclass(frozen=True)
class Issue:
    selection_sha256: str
    issued_at: str
    identities: tuple[PolicyIdentity, ...]
    reference_rows: int
    learned_rows: int


@dataclass(frozen=True)
class Ledger:
    selection_sha256: str
    created_at: str
    identities: tuple[PolicyIdentity, ...]
    historical_policy_backdated: bool = False
    legacy_exposed_forecasts_used: bool = False


def identities(values: tuple[PolicyIdentity, ...]) -> tuple[PolicyIdentity, ...]:
    if type(values) is not tuple or not values:
        raise ValueError("policy identities require a nonempty immutable tuple")
    for value in values:
        if not isinstance(value, PolicyIdentity):
            raise ValueError("invalid policy identity")
        value.validate()
    if len({value.league for value in values}) != len(values):
        raise ValueError("duplicate league policy")
    return tuple(sorted(values, key=lambda value: value.league))


def verify_binding(selection: Selection, issue: Issue, ledger: Ledger) -> dict:
    """Reject a different identity, forward selection, or invented earlier clock."""
    digest(selection.sha256)
    if type(selection.seasons) is not tuple or not selection.seasons:
        raise ValueError("selection seasons require a nonempty immutable tuple")
    if any(type(year) is not int or year < 2023 or year >= 2026 for year in selection.seasons):
        raise ValueError("forward outcomes or unsupported seasons in selection")
    if len(set(selection.seasons)) != len(selection.seasons):
        raise ValueError("duplicate historical season")
    selected = identities(selection.identities)
    if identities(issue.identities) != selected or identities(ledger.identities) != selected:
        raise ValueError("selected, served and recorded policies differ")
    if digest(issue.selection_sha256) != selection.sha256 or digest(ledger.selection_sha256) != selection.sha256:
        raise ValueError("selection content identity differs")
    if not instant(selection.available_at) <= instant(issue.issued_at) <= instant(ledger.created_at):
        raise ValueError("selection, issue and ledger clocks are out of order")
    if ledger.historical_policy_backdated is not False or ledger.legacy_exposed_forecasts_used is not False:
        raise ValueError("retrospective policy substitution is prohibited")
    count(issue.reference_rows); count(issue.learned_rows)
    kinds = {value.policy_kind for value in selected}
    if issue.learned_rows and kinds == {"market_fallback"}:
        raise ValueError("market references counted as learned forecasts")
    if issue.reference_rows and kinds == {"learned"}:
        raise ValueError("learned forecasts counted as market references")
    return {"status": "LINEAGE_MATCHES", "selection_sha256": selection.sha256,
            "leagues": [value.league for value in selected],
            "reference_rows": issue.reference_rows, "learned_rows": issue.learned_rows,
            "economic_readiness_assessed": False, "predictive_superiority_assessed": False}


def _exact(value: dict, fields: set[str], context: str) -> None:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"unexpected public {context} fields")


def validate_public_receipt(data: dict) -> dict:
    """Reconcile a sanitized receipt; private source bytes are not public inputs."""
    _exact(data, {"schema", "as_of_local", "owner_return_sha256", "owner_source_sha256", "owner",
                  "selection", "issue", "ledger", "performance_stages", "limitations"}, "receipt")
    if data["schema"] != "sports-edge-lab.public-v126-execution-v1":
        raise ValueError("unsupported public receipt schema")
    digest(data["owner_return_sha256"]); digest(data["owner_source_sha256"])
    _exact(data["owner"], {"status", "new_fits", "fit_attempts", "owner_tests", "test_workers", "tests_seconds",
        "worker_seconds", "supervised_seconds", "peak_rss_bytes", "working_disk_bytes", "retained_native_cells",
        "retained_fusion_fits", "retained_expert_fits", "archive_member_pins", "actual_wagers", "automatic_promotions"}, "owner")
    owner = data["owner"]
    if owner["status"] != "SUCCESS" or owner["new_fits"] != 0 or owner["fit_attempts"] != 0:
        raise ValueError("this V126 receipt records a completed zero-fit run")
    for name, value in owner.items():
        if name == "status":
            continue
        if name.endswith("seconds"):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("invalid duration")
        else:
            count(value)
    if owner["actual_wagers"] or owner["automatic_promotions"]:
        raise ValueError("this snapshot contains no orders or promotions")
    if not owner["owner_tests"] or not owner["test_workers"] or not owner["archive_member_pins"]:
        raise ValueError("a verified receipt requires executed checks and verified members")
    if owner["tests_seconds"] > owner["worker_seconds"] or owner["worker_seconds"] > owner["supervised_seconds"]:
        raise ValueError("duration nesting is inconsistent")
    selected, issued, recorded = data["selection"], data["issue"], data["ledger"]
    _exact(selected, {"sha256", "available_at", "allowed_seasons", "current_outcomes_used", "identities"}, "selection")
    _exact(issued, {"selection_sha256", "issued_at", "reference_rows_by_league", "learned_policy_rows",
        "separate_research_forecast_rows", "identity_matches_selection", "historical_publication_claimed"}, "issue")
    _exact(recorded, {"selection_sha256", "created_at", "backdated", "legacy_exposed_forecasts_used", "native_week_rows",
        "schedule_game_rows", "strict_forecast_eligible_games", "historical_profit", "execution_ready"}, "ledger")
    if selected["current_outcomes_used"] is not False or issued["historical_publication_claimed"] is not False:
        raise ValueError("forward selection or invented historical availability")
    if issued["identity_matches_selection"] is not True:
        raise ValueError("owner identity audit did not pass")
    policies = []
    for value in selected["identities"]:
        _exact(value, {"league", "policy_id", "policy_kind", "rule_sha256", "learned_policy_qualified"}, "policy")
        policies.append(PolicyIdentity(**value))
    policy_tuple = tuple(policies)
    if set(issued["reference_rows_by_league"]) != {value.league for value in policies}:
        raise ValueError("issue scope differs from selected leagues")
    for value in issued["reference_rows_by_league"].values():
        count(value)
    count(issued["separate_research_forecast_rows"])
    for name in ("native_week_rows", "schedule_game_rows", "strict_forecast_eligible_games"):
        count(recorded[name])
    if recorded["strict_forecast_eligible_games"] or recorded["historical_profit"] is not None or recorded["execution_ready"] is not False:
        raise ValueError("this snapshot has unavailable executable profit, not zero profit")
    result = verify_binding(
        Selection(selected["sha256"], selected["available_at"], tuple(selected["allowed_seasons"]), policy_tuple),
        Issue(issued["selection_sha256"], issued["issued_at"], policy_tuple,
              sum(issued["reference_rows_by_league"].values()), issued["learned_policy_rows"]),
        Ledger(recorded["selection_sha256"], recorded["created_at"], policy_tuple,
               recorded["backdated"], recorded["legacy_exposed_forecasts_used"]))
    seen = set()
    for stage in data["performance_stages"]:
        _exact(stage, {"stage", "seconds"}, "performance")
        if not isinstance(stage["stage"], str) or stage["stage"] in seen:
            raise ValueError("duplicate or invalid stage")
        seen.add(stage["stage"])
        if type(stage["seconds"]) not in (int, float) or not math.isfinite(stage["seconds"]) or stage["seconds"] < 0:
            raise ValueError("invalid stage duration")
    if sum(stage["seconds"] for stage in data["performance_stages"]) > owner["worker_seconds"] + .001:
        raise ValueError("exclusive stages exceed worker duration")
    if not isinstance(data["limitations"], list) or any(not isinstance(value, str) for value in data["limitations"]):
        raise ValueError("limitations must be public prose")
    return {**result, "owner_tests": owner["owner_tests"], "new_fits": owner["new_fits"],
            "separate_research_forecast_rows": issued["separate_research_forecast_rows"],
            "historical_profit": None, "private_artifacts_reproduced": False}


def demo() -> dict:
    """Invented identities, with no model fitting, network calls or orders."""
    sha = hashlib.sha256(b"invented immutable selection").hexdigest()
    rule = hashlib.sha256(b"invented benchmark rule").hexdigest()
    policy = (PolicyIdentity("nfl", "invented_market_reference", rule, "market_fallback", False),)
    selected = Selection(sha, "2026-01-01T00:00:00Z", (2023, 2024, 2025), policy)
    issued = Issue(sha, "2026-01-02T00:00:00Z", policy, 2, 0)
    ledger = Ledger(sha, "2026-01-02T00:01:00Z", policy)
    return {"input_kind": "INVENTED", **verify_binding(selected, issued, ledger)}


if __name__ == "__main__":
    print(json.dumps({"synthetic_demo": demo(), "sanitized_owner_receipt": validate_public_receipt(json.loads(SOURCE.read_text()))}, indent=2))
