"""Invented-only historical-reference and possession contracts.

This credential-free teaching module contains no actual quotes, picks, models,
private storage paths, provider calls or executable betting recommendations.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
import hashlib
import json

from .contracts import number, timestamp


FIELDS = {"data_kind", "event", "provider", "product", "method", "side", "target",
          "line", "settlement", "tip_at", "quoted_at", "acquired_at", "probability",
          "tick_window_exhausted", "sampling_resolution_seconds"}
PROVIDERS = {"draftkings", "kalshi", "polymarket_us", "polymarket_international"}
POLICIES = {"LATEST_BEFORE_TIP": 0, "T60": 60, "T120": 120}


def invented_quote(**changes):
    row = dict(data_kind="INVENTED", event="invented-game-01", provider="kalshi",
               product="full_game_winner", method="historical_midpoint", side="home",
               target="winner", line=None, settlement="includes_overtime",
               tip_at="2035-11-01T20:00:00Z", quoted_at="2035-11-01T18:59:00Z",
               acquired_at="2035-11-03T12:00:00Z", probability=0.61,
               tick_window_exhausted=False, sampling_resolution_seconds=60)
    row.update(changes)
    return row


def validate(row):
    if set(row) != FIELDS:
        raise ValueError("only allowlisted invented reference fields are supported")
    if row["data_kind"] != "INVENTED":
        raise ValueError("this public demonstration accepts invented observations only")
    if row["provider"] not in PROVIDERS:
        raise ValueError("provider/product scope must be explicit")
    if row["target"] != "winner" or row["side"] != "home" or row["line"] is not None:
        raise ValueError("this example compares home-side full-game winner probabilities")
    for key in ("event", "product", "method"):
        if not isinstance(row[key], str) or not row[key]:
            raise ValueError("complete reference identity is required")
    if row["settlement"] is not None and not isinstance(row["settlement"], str):
        raise ValueError("settlement must be a definition or unknown")
    quote, acquired = timestamp(row["quoted_at"]), timestamp(row["acquired_at"])
    timestamp(row["tip_at"])
    if acquired < quote:
        raise ValueError("acquisition cannot predate the recorded source quote")
    number(row["probability"], lower=0, upper=1)
    number(row["sampling_resolution_seconds"], lower=0)
    if type(row["tick_window_exhausted"]) is not bool:
        raise ValueError("window exhaustion needs an explicit boolean")
    return deepcopy(row)


def reference_panel(rows, policy):
    """Keep recoverable history visible; qualify its uses separately.

    Selection is based solely on source quote clocks. Outcomes are not accepted
    by the schema. Each product/method/settlement keeps its own panel.
    """
    if policy not in POLICIES:
        raise ValueError("an explicit latest-before-tip, T60 or T120 policy is required")
    selected = {}
    for source in rows:
        row = validate(source)
        tip, quote = timestamp(row["tip_at"]), timestamp(row["quoted_at"])
        cutoff = tip - timedelta(minutes=POLICIES[policy])
        if quote >= tip or quote > cutoff:
            continue
        key = tuple(row[k] for k in ("event", "provider", "product", "method", "side", "target", "line", "settlement", "tip_at"))
        old = selected.get(key)
        if old and timestamp(old["quoted_at"]) == quote:
            if old != row:
                raise ValueError("same-clock conflict requires explicit resolution")
            continue  # exact reuse adds no observation or forecast credit
        if old is None or timestamp(old["quoted_at"]) < quote:
            selected[key] = row
    output = []
    for row in selected.values():
        tip, quote = timestamp(row["tip_at"]), timestamp(row["quoted_at"])
        cutoff = tip - timedelta(minutes=POLICIES[policy])
        acquired = timestamp(row["acquired_at"])
        known_settlement = bool(row["settlement"])
        output.append(dict(row, quote_policy=policy, cutoff_at=cutoff.isoformat(),
            historical_reference_comparison_eligible=known_settlement,
            original_possession_before_cutoff=acquired <= cutoff,
            prospective_comparison_eligible=known_settlement and acquired <= cutoff,
            latest_tick_exhaustiveness_proven=row["tick_window_exhausted"] and row["sampling_resolution_seconds"] == 0,
            new_forecast_credit=0, new_allocation=0, profit=None, roi=None))
    return sorted(output, key=lambda r:(r["event"], r["provider"], r["method"], r["product"]))


def inventory_view(events, panels):
    """Outer inventory: no quote does not cause a game to disappear."""
    if any(not isinstance(e, str) or not e for e in events) or len(set(events)) != len(events):
        raise ValueError("unique nonempty inventory identities required")
    if any(row["event"] not in events for row in panels):
        raise ValueError("unjoined reference must be reconciled with the inventory")
    return [dict(event=event, references=deepcopy([r for r in panels if r["event"] == event]),
                 coverage="OBSERVED_REFERENCE" if any(r["event"] == event for r in panels) else "NOT_RECOVERED_NOT_PROOF_OF_NO_MARKET")
            for event in events]


def pack_local_view(payload):
    """Exact-byte integrity envelope; not a signature or authenticity claim."""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return dict(payload_json=raw, sha256=hashlib.sha256(raw.encode()).hexdigest(),
                authenticity_proven=False, upload_required=False)


def unpack_local_view(envelope):
    raw = envelope["payload_json"]
    if not isinstance(raw, str) or len(raw.encode()) > 1_000_000:
        raise ValueError("bounded JSON payload required")
    if hashlib.sha256(raw.encode()).hexdigest() != envelope["sha256"]:
        raise ValueError("SHA-256 mismatch; retain the previous view")
    return json.loads(raw)


def walkthrough():
    early = invented_quote()
    close = invented_quote(quoted_at="2035-11-01T19:59:00Z", probability=0.58)
    return dict(data_kind="INVENTED", provider_requests=0, estimator_fits=0,
                cutoff_panel=reference_panel([early, close], "T60"),
                latest_panel=reference_panel([early, close], "LATEST_BEFORE_TIP"),
                inventory=inventory_view(["invented-game-01", "invented-game-02"], reference_panel([early], "T60")))


if __name__ == "__main__":
    print(json.dumps(walkthrough(), indent=2, sort_keys=True))
