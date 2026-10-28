"""Credential-free historical-odds catalog, recovery plan and durable quota journal.

This public example accepts a documented normalized envelope, not vendor JSON.
It never opens a socket, reads a secret, fits a model, or spends a provider credit.
All built-in data and authorization receipts are invented. See the companion doc
for the trusted ingestion boundary and the deliberately supported endpoint scope.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Iterable, Mapping

SPORT_KEYS = {"nba": "basketball_nba", "ncaam": "basketball_ncaab", "ncaaw": "basketball_wncaab"}
FEATURED = frozenset(("h2h", "spreads", "totals"))
REGIONS = frozenset(("us", "us2", "uk", "eu", "au"))
SCHEMA = "public.normalized_historical_odds.v1"


def encoded(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value) -> str:
    return hashlib.sha256(encoded(value)).hexdigest()


def pin(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("exact lowercase SHA-256 required")
    return value


def instant(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("explicit timestamp string required")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone-aware timestamp required")
    return parsed.astimezone(timezone.utc)


def iso(value: str) -> str:
    return instant(value).isoformat().replace("+00:00", "Z")


def integer(value, *, positive=False) -> int:
    if type(value) is not int or value < (1 if positive else 0):
        raise ValueError("nonnegative integer required" if not positive else "positive integer required")
    return value


def atomic_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", value):
        raise ValueError("opaque atomic identity required; URLs and credentials are not inputs")
    return value


def keys(values: tuple[str, ...], allowed: frozenset[str]) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values or len(set(values)) != len(values) or not set(values) <= allowed:
        raise ValueError("nonempty unique supported keys required")
    return tuple(sorted(values))


@dataclass(frozen=True)
class SnapshotRequest:
    sport_key: str
    at: str
    markets: tuple[str, ...]
    regions: tuple[str, ...]

    def __post_init__(self):
        if self.sport_key not in SPORT_KEYS.values():
            raise ValueError("unsupported sport identity")
        object.__setattr__(self, "at", iso(self.at))
        object.__setattr__(self, "markets", keys(self.markets, FEATURED))
        object.__setattr__(self, "regions", keys(self.regions, REGIONS))

    @property
    def identity(self) -> str:
        return digest({"endpoint": "historical_featured_region_mode", **asdict(self)})

    @property
    def credit_ceiling(self) -> int:
        # Verified public contract: regional historical featured endpoint only.
        # Actual response headers remain authoritative, including zero-cost empty data.
        return 10 * len(self.markets) * len(self.regions)


@dataclass(frozen=True)
class Need:
    league: str
    event_id: str
    provider_event_id: str
    home_id: str
    away_id: str
    tipoff: str
    cutoff: str
    binding_receipt_sha256: str
    markets: tuple[str, ...] = ("h2h",)
    regions: tuple[str, ...] = ("us",)

    def __post_init__(self):
        if self.league not in SPORT_KEYS:
            raise ValueError("explicit league namespace required")
        for value in (self.event_id, self.provider_event_id, self.home_id, self.away_id):
            atomic_id(value)
        if self.home_id == self.away_id or instant(self.cutoff) >= instant(self.tipoff):
            raise ValueError("distinct teams and a pregame cutoff required")
        pin(self.binding_receipt_sha256)
        object.__setattr__(self, "tipoff", iso(self.tipoff))
        object.__setattr__(self, "cutoff", iso(self.cutoff))
        object.__setattr__(self, "markets", keys(self.markets, FEATURED))
        object.__setattr__(self, "regions", keys(self.regions, REGIONS))

    @property
    def identity(self) -> str:
        return digest(asdict(self))


def _outcomes(market: str, outcomes) -> None:
    if not isinstance(outcomes, list) or len(outcomes) != 2:
        raise ValueError("exact paired outcomes required")
    sides = {o.get("side") for o in outcomes}
    if sides != ({"over", "under"} if market == "totals" else {"home", "away"}):
        raise ValueError("paired outcome identities do not match market")
    for row in outcomes:
        price = row.get("decimal_price")
        if type(price) not in (float, int) or not math.isfinite(price) or price <= 1:
            raise ValueError("finite decimal price above one required")
    if market in {"spreads", "totals"}:
        lines = [row.get("line") for row in outcomes]
        if any(type(v) not in (float, int) or not math.isfinite(v) for v in lines):
            raise ValueError("finite paired lines required")
        if (market == "spreads" and sum(lines) != 0) or (market == "totals" and (lines[0] != lines[1] or lines[0] <= 0)):
            raise ValueError("opposing spreads or equal positive totals required")


class Catalog:
    """Content-verified normalized originals; retain aliases and request receipts.

    The caller must inventory its declared relevant prefixes, parse raw originals
    with a separately audited adapter, and only then seal the scoped inventory.
    A SHA-256 proves bytes against a receipt, not truth or provider authenticity.
    """
    def __init__(self):
        self._objects: dict[str, dict] = {}
        self._receipts: dict[tuple[str, str, str, str], dict] = {}
        self.scope_receipt_sha256: str | None = None

    def add(self, alias: str, payload: bytes, expected_sha256: str, request: SnapshotRequest, captured_at: str):
        if self.scope_receipt_sha256:
            raise ValueError("sealed inventory is immutable; create a new version")
        atomic_id(alias)
        pin(expected_sha256)
        if not isinstance(payload, bytes) or hashlib.sha256(payload).hexdigest() != expected_sha256:
            raise ValueError("catalog content hash mismatch")
        data = json.loads(payload)
        if data.get("schema") != SCHEMA or data.get("sport_key") != request.sport_key:
            raise ValueError("normalized schema and request sport must match")
        snapshot = instant(data["snapshot_at"])
        if snapshot > instant(request.at) or snapshot > instant(captured_at):
            raise ValueError("snapshot cannot follow request date or retrieval")
        records = data.get("records")
        if not isinstance(records, list):
            raise ValueError("normalized records list required")
        seen = set()
        for row in records:
            for field in ("event_id", "home_id", "away_id", "bookmaker_id"):
                atomic_id(row[field])
            market, region = row["market"], row["region"]
            if market not in request.markets or region not in request.regions:
                raise ValueError("returned observation outside requested scope")
            if row["home_id"] == row["away_id"]:
                raise ValueError("distinct source teams required")
            instant(row["tipoff"])
            if instant(row["quote_updated_at"]) > snapshot:
                raise ValueError("quote update cannot follow archive snapshot")
            _outcomes(market, row["outcomes"])
            key = (row["event_id"], row["bookmaker_id"], market, region)
            if key in seen:
                raise ValueError("ambiguous duplicate observation in one snapshot")
            seen.add(key)
        self._objects.setdefault(expected_sha256, data)
        receipt_key = (alias, expected_sha256, request.identity, iso(captured_at))
        self._receipts.setdefault(receipt_key, {"alias": alias, "sha256": expected_sha256,
            "request": asdict(request), "request_sha256": request.identity, "captured_at": iso(captured_at)})

    def seal(self, scope_receipt_sha256: str, *, unresolved_objects: int = 0):
        pin(scope_receipt_sha256)
        integer(unresolved_objects)
        if unresolved_objects:
            raise ValueError("unclassified inventory objects prevent gap-driven requests")
        if self.scope_receipt_sha256 and self.scope_receipt_sha256 != scope_receipt_sha256:
            raise ValueError("inventory scope receipt cannot be replaced")
        self.scope_receipt_sha256 = scope_receipt_sha256

    def summary(self):
        return {"content_objects": len(self._objects), "retrieval_receipts": len(self._receipts),
            "aliases": len({r["alias"] for r in self._receipts.values()}),
            "normalized_observations": sum(len(v["records"]) for v in self._objects.values()),
            "scope_receipt_sha256": self.scope_receipt_sha256}

    def request_already_captured(self, request: SnapshotRequest) -> bool:
        for receipt in self._receipts.values():
            saved = receipt["request"]
            if (saved["sport_key"] == request.sport_key and iso(saved["at"]) == request.at
                and set(saved["markets"]) >= set(request.markets) and set(saved["regions"]) >= set(request.regions)):
                return True
        return False

    def usable(self, need: Need, market: str, region: str, *, freshness_seconds: int):
        integer(freshness_seconds, positive=True)
        cutoff = instant(need.cutoff)
        candidates = []
        for source_sha, data in sorted(self._objects.items()):
            snapshot = instant(data["snapshot_at"])
            if data["sport_key"] != SPORT_KEYS[need.league] or snapshot > cutoff:
                continue
            for row in data["records"]:
                if (row["event_id"], row["home_id"], row["away_id"], instant(row["tipoff"]), row["market"], row["region"]) != (
                    need.provider_event_id, need.home_id, need.away_id, instant(need.tipoff), market, region):
                    continue
                update = instant(row["quote_updated_at"])
                if timedelta(0) <= cutoff - update <= timedelta(seconds=freshness_seconds):
                    candidates.append({"content_sha256": source_sha, "snapshot_at": iso(data["snapshot_at"]),
                        "quote_updated_at": iso(row["quote_updated_at"]), "bookmaker_id": row["bookmaker_id"],
                        "evidence_tier": "provider_historical_archive_not_prospective_capture"})
        # Several bookmaker observations satisfy one event/market/region cell.
        return sorted(candidates, key=lambda row: (row["quote_updated_at"], row["content_sha256"], row["bookmaker_id"]))


@dataclass(frozen=True)
class Capability:
    sport_key: str
    historical_from: str
    markets: tuple[str, ...]
    regions: tuple[str, ...]
    entitlement_confirmed: bool
    verified_at: str
    valid_until: str
    evidence_sha256: str

    def __post_init__(self):
        if self.sport_key not in SPORT_KEYS.values() or type(self.entitlement_confirmed) is not bool:
            raise ValueError("explicit supported sport and entitlement state required")
        pin(self.evidence_sha256)
        keys(self.markets, FEATURED); keys(self.regions, REGIONS)
        instant(self.historical_from)
        if instant(self.verified_at) >= instant(self.valid_until):
            raise ValueError("capability evidence must have a bounded validity interval")

    def permits(self, request: SnapshotRequest, now: str):
        return (self.entitlement_confirmed and self.sport_key == request.sport_key
            and instant(self.verified_at) <= instant(now) < instant(self.valid_until)
            and instant(self.historical_from) <= instant(request.at) <= instant(now)
            and set(request.markets) <= set(self.markets) and set(request.regions) <= set(self.regions))


@dataclass(frozen=True)
class Quota:
    remaining_credits: int
    observed_at: str
    receipt_sha256: str

    def __post_init__(self):
        integer(self.remaining_credits); instant(self.observed_at); pin(self.receipt_sha256)

    @classmethod
    def from_headers(cls, headers: Mapping[str, str], observed_at: str, receipt_sha256: str):
        value = {k.lower(): v for k, v in headers.items()}.get("x-requests-remaining")
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value):
            raise ValueError("missing or invalid remaining-credit header")
        return cls(int(value), observed_at, receipt_sha256)

    def fresh(self, now: str, *, max_age_seconds: int = 300):
        integer(max_age_seconds, positive=True)
        return timedelta(0) <= instant(now) - instant(self.observed_at) <= timedelta(seconds=max_age_seconds)


@dataclass(frozen=True)
class Budget:
    request_limit: int
    requests_used: int
    credit_limit: int
    credits_charged_or_reserved: int
    authorization_sha256: str | None = None

    def __post_init__(self):
        for value in (self.request_limit, self.requests_used, self.credit_limit, self.credits_charged_or_reserved):
            integer(value)
        if self.authorization_sha256 is not None:
            pin(self.authorization_sha256)
        if self.requests_used > self.request_limit or self.credits_charged_or_reserved > self.credit_limit:
            raise ValueError("existing cumulative usage exceeds declared ceiling")


def plan_recovery(needs: Iterable[Need], catalog: Catalog, capabilities: Iterable[Capability],
                  budget: Budget, quota: Quota | None, now: str, *, freshness_seconds=900) -> dict:
    """Identify missing cells, coalesce exact queries, then apply independent gates.

    Empty or stale results from an already captured exact query remain uncovered;
    they do not authorize an identical historical request on every restart.
    """
    instant(now); integer(freshness_seconds, positive=True)
    if not catalog.scope_receipt_sha256:
        raise ValueError("inspect and seal a declared source inventory before planning")
    inputs = tuple(needs)
    unique = {need.identity: need for need in inputs}
    scope_identity = {}
    for need in unique.values():
        key = (need.league, need.event_id, need.cutoff)
        binding = (need.provider_event_id, need.home_id, need.away_id, need.tipoff, need.binding_receipt_sha256)
        if key in scope_identity and scope_identity[key] != binding:
            raise ValueError("conflicting event binding in one requested scope")
        scope_identity[key] = binding
    capabilities = tuple(capabilities)
    cells, groups, seen_cells = [], {}, set()
    for need in sorted(unique.values(), key=lambda n: n.identity):
        for region in need.regions:
            for market in need.markets:
                cell_key = (need.league, need.event_id, need.cutoff, market, region)
                if cell_key in seen_cells:
                    continue
                seen_cells.add(cell_key)
                hits = catalog.usable(need, market, region, freshness_seconds=freshness_seconds)
                cell = {"need_sha256": need.identity, "event_id": need.event_id, "league": need.league,
                    "market": market, "region": region, "status": "cached_usable" if hits else "missing_usable_observation",
                    "observations": hits, "binding_receipt_sha256": need.binding_receipt_sha256}
                cells.append(cell)
                if not hits:
                    key = (SPORT_KEYS[need.league], need.cutoff, region)
                    group = groups.setdefault(key, {"markets": set(), "needs": set()})
                    group["markets"].add(market); group["needs"].add(need.identity)
    requests, deferred = [], []
    for (sport, at, region), group in sorted(groups.items()):
        request = SnapshotRequest(sport, at, tuple(sorted(group["markets"])), (region,))
        row = {"request_sha256": request.identity, **asdict(request), "credit_ceiling": request.credit_ceiling,
            "need_sha256s": sorted(group["needs"])}
        if catalog.request_already_captured(request):
            deferred.append({**row, "reason": "exact_request_already_captured_but_no_eligible_quote"})
        elif not any(cap.permits(request, now) for cap in capabilities):
            deferred.append({**row, "reason": "historical_support_or_entitlement_unverified_or_out_of_range"})
        else:
            requests.append(row)
    request_count = len(requests); credit_ceiling = sum(row["credit_ceiling"] for row in requests)
    blockers = []
    if requests:
        if budget.authorization_sha256 is None:
            blockers.append("explicit_incremental_request_and_credit_authorization_missing")
        if request_count > budget.request_limit - budget.requests_used:
            blockers.append("cumulative_request_ceiling")
        if credit_ceiling > budget.credit_limit - budget.credits_charged_or_reserved:
            blockers.append("cumulative_credit_ceiling")
        if quota is None or not quota.fresh(now):
            blockers.append("fresh_verified_provider_remaining_quota_missing")
        elif credit_ceiling > quota.remaining_credits:
            blockers.append("provider_credit_allowance")
    result = {"schema": "public.odds_recovery_plan.v1", "network_requests": 0, "provider_credits_spent": 0,
        "inventory": catalog.summary(), "input_needs": len(inputs), "unique_needs": len(unique),
        "expected_cells": len(cells), "covered_cells": sum(row["status"] == "cached_usable" for row in cells),
        "cells": cells, "requests": requests, "deferred": deferred,
        "planned_requests": request_count, "planned_credit_ceiling": credit_ceiling,
        "budget": asdict(budget), "quota": asdict(quota) if quota else None,
        "blocked_by": blockers, "dispatch_permitted_by_example_contract": bool(requests) and not blockers,
        "network_dispatch_implemented": False,
        "uncovered_is_not_proof_no_bookmaker_offered_game": True}
    return {**result, "plan_sha256": digest(result)}


class QuotaJournal:
    """Single-host, flock-protected, append-only reservation/receipt state machine.

    Persist reservation before dispatch; a lost response keeps its full credit
    debit. Reusing an attempt ID never creates another reservation. A partial or
    edited journal fails closed. This example does not implement network dispatch.
    """
    def __init__(self, path: Path, budget: Budget):
        if budget.authorization_sha256 is None:
            raise ValueError("explicit budget authorization receipt required")
        self.path, self.budget = Path(path), budget
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _transact(self, operation, payload):
        import fcntl  # POSIX demonstration; no cloud, environment or credential access.
        with self.path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.seek(0); raw = handle.read()
            if raw and not raw.endswith("\n"):
                raise ValueError("incomplete journal tail; no automatic budget reset")
            events = []; previous = "0" * 64
            for line in raw.splitlines():
                row = json.loads(line)
                body = {k: v for k, v in row.items() if k != "sha256"}
                if row.get("previous") != previous or row.get("sha256") != digest(body):
                    raise ValueError("journal chain mismatch")
                previous = row["sha256"]; events.append(row)
            def append(kind, value):
                nonlocal previous
                body = {"previous": previous, "kind": kind, "value": value}
                row = {**body, "sha256": digest(body)}
                handle.seek(0, os.SEEK_END); handle.write(encoded(row).decode() + "\n"); handle.flush(); os.fsync(handle.fileno())
                previous = row["sha256"]; events.append(row)
            if not events:
                append("budget", asdict(self.budget))
            if events[0]["kind"] != "budget" or events[0]["value"] != asdict(self.budget):
                raise ValueError("journal budget identity changed; cumulative usage cannot reset")
            attempts = {}; used = self.budget.requests_used; charged = self.budget.credits_charged_or_reserved
            cost_contract_changed = False
            for event in events[1:]:
                kind, value = event["kind"], event["value"]
                if kind == "reserved":
                    atomic_id(value["attempt_id"]); pin(value["request_sha256"])
                    integer(value["credit_ceiling"], positive=True); instant(value["reserved_at"])
                    if value["attempt_id"] in attempts:
                        raise ValueError("duplicate journal reservation")
                    attempts[value["attempt_id"]] = {**value, "status": "reserved"}
                    used += 1; charged += value["credit_ceiling"]
                elif kind == "completed":
                    item = attempts.get(value["attempt_id"])
                    integer(value["actual_credits"]); pin(value["response_sha256"])
                    if not item or item["status"] != "reserved":
                        raise ValueError("completion without unique pending reservation")
                    if instant(value["observed_at"]) < instant(item["reserved_at"]):
                        raise ValueError("completion observation precedes reservation")
                    cost_contract_changed |= value["actual_credits"] > item["credit_ceiling"]
                    charged += value["actual_credits"] - item["credit_ceiling"]
                    item.update(value, status="completed")
                else:
                    raise ValueError("unknown journal event")
            breached = used > self.budget.request_limit or charged > self.budget.credit_limit
            if operation == "reserve":
                attempt, request, quota, now = payload
                atomic_id(attempt)
                identity = {"attempt_id": attempt, "request_sha256": request.identity, "credit_ceiling": request.credit_ceiling}
                old = attempts.get(attempt)
                if old:
                    if any(old[k] != v for k, v in identity.items()):
                        raise ValueError("attempt ID reused for different request")
                    return {"new_reservation": False, **old}
                if cost_contract_changed:
                    raise ValueError("observed cost exceeded contract; investigate before another reservation")
                if breached or used + 1 > self.budget.request_limit or charged + request.credit_ceiling > self.budget.credit_limit:
                    raise ValueError("cumulative quota ceiling blocks reservation")
                if quota is None or not quota.fresh(now):
                    raise ValueError("fresh provider quota evidence required")
                # Other pending attempts can be absent from the provider header.
                unreflected = sum(a["credit_ceiling"] if a["status"] == "reserved" else a["actual_credits"]
                    for a in attempts.values()
                    if a["status"] == "reserved" or instant(a["observed_at"]) >= instant(quota.observed_at))
                if request.credit_ceiling + unreflected > quota.remaining_credits:
                    raise ValueError("provider quota cannot cover pending and new requests")
                reservation = {**identity, "reserved_at": iso(now)}
                append("reserved", reservation)
                return {"new_reservation": True, **reservation, "status": "reserved"}
            if operation == "complete":
                attempt, actual, response_sha, observed_at = payload
                atomic_id(attempt); integer(actual); pin(response_sha); observed_at = iso(observed_at)
                old = attempts.get(attempt)
                value = {"attempt_id": attempt, "actual_credits": actual, "response_sha256": response_sha, "observed_at": observed_at}
                if old is None:
                    raise ValueError("completion requires reservation")
                if instant(observed_at) < instant(old["reserved_at"]):
                    raise ValueError("completion observation precedes reservation")
                if old["status"] == "completed":
                    if any(old[k] != v for k, v in value.items()):
                        raise ValueError("completed response is immutable")
                    return {"new_receipt": False, **old}
                append("completed", value)
                # Higher-than-estimated usage is preserved as actual spend, then
                # stops subsequent dispatch. It is never clamped to the estimate.
                return {"new_receipt": True, **value, "unexpected_cost": actual > old["credit_ceiling"]}
            return {"requests_used": used, "credits_charged_or_reserved": charged,
                "pending_attempts": sum(a["status"] == "reserved" for a in attempts.values()),
                "completed_attempts": sum(a["status"] == "completed" for a in attempts.values()),
                "budget_breached": breached, "cost_contract_changed": cost_contract_changed, "attempts": attempts, "journal_sha256": previous}

    def reserve(self, attempt: str, request: SnapshotRequest, quota: Quota | None, now: str):
        return self._transact("reserve", (attempt, request, quota, now))

    def complete(self, attempt: str, actual_credits: int, response_sha256: str, observed_at: str):
        return self._transact("complete", (attempt, actual_credits, response_sha256, observed_at))

    def state(self):
        return self._transact("state", None)


def walkthrough() -> dict:
    """One cached game + two invented same-cutoff gaps = one proposed request."""
    now = "2026-10-28T20:00:00Z"
    earlier = "2025-01-01T19:00:00Z"
    needs = [Need("nba", f"fixture-game-{n}", f"fixture-provider-{n}", f"fixture-home-{n}", f"fixture-away-{n}",
        "2025-01-01T20:00:00Z", earlier, digest({"invented_binding": n}), ("h2h", "totals")) for n in range(3)]
    request = SnapshotRequest("basketball_nba", earlier, ("h2h", "totals"), ("us",))
    # This earlier query already contains usable game-zero observations; it does
    # not assert the later exact query was captured for the other two games.
    cached_request = SnapshotRequest("basketball_nba", "2025-01-01T18:55:00Z", ("h2h", "totals"), ("us",))
    rows = []
    for market in ("h2h", "totals"):
        outcomes = ([{"side": "home", "decimal_price": 1.9}, {"side": "away", "decimal_price": 1.95}] if market == "h2h" else
            [{"side": "over", "decimal_price": 1.9, "line": 200.0}, {"side": "under", "decimal_price": 1.9, "line": 200.0}])
        rows.append({"event_id": "fixture-provider-0", "home_id": "fixture-home-0", "away_id": "fixture-away-0",
            "tipoff": needs[0].tipoff, "bookmaker_id": "fixture-book", "market": market, "region": "us",
            "quote_updated_at": "2025-01-01T18:53:00Z", "outcomes": outcomes})
    payload = encoded({"schema": SCHEMA, "sport_key": "basketball_nba", "snapshot_at": cached_request.at, "records": rows})
    catalog = Catalog(); content_pin = hashlib.sha256(payload).hexdigest()
    for alias in ("fixture-archive-a", "fixture-archive-b"):
        catalog.add(alias, payload, content_pin, cached_request, now)
    catalog.seal(digest({"invented_scope": "two-fixture-archives"}))
    capability = Capability("basketball_nba", "2020-07-01T00:00:00Z", ("h2h", "totals"), ("us",), True,
        "2026-10-28T19:59:00Z", "2026-10-28T21:00:00Z", digest({"invented_entitlement": True}))
    budget = Budget(4, 1, 100, 10, digest({"invented_approval": True}))
    quota = Quota(80, now, digest({"invented_header": 80}))
    plan = plan_recovery(needs, catalog, [capability], budget, quota, now)
    assert plan["planned_requests"] == 1 and plan["planned_credit_ceiling"] == request.credit_ceiling == 20
    return {"synthetic": True, "real_records_recovered": 0, "actual_requests": 0, "actual_fits": 0,
        "purpose": "public engineering contract; not an owner run or subscription verification", "plan": plan}


if __name__ == "__main__":
    print(json.dumps(walkthrough(), indent=2, sort_keys=True))
