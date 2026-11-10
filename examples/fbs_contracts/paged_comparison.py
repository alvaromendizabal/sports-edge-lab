"""Credential-free, invented demonstration of complete paged comparisons.

This is generic bookkeeping, not the private FBS research implementation.
Every sample name and loss in ``demo_pages`` is fictional. No model is fitted,
no provider is contacted, and no real forecasting result is reproduced.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable, Mapping


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class Sample:
    candidate: str
    event: str
    loss: float

    def as_dict(self) -> dict:
        if not self.candidate or not self.event:
            raise ValueError("A candidate and an event are required")
        if not isinstance(self.loss, (int, float)) or isinstance(self.loss, bool):
            raise ValueError("A finite numeric loss is required")
        if not math.isfinite(self.loss):
            raise ValueError("A finite numeric loss is required")
        return {"candidate": self.candidate, "event": self.event, "loss": self.loss}


def seal_page(page_id: str, samples: Iterable[Sample]) -> dict:
    if not page_id:
        raise ValueError("A page identity is required")
    body = {"page_id": page_id, "samples": [row.as_dict() for row in samples]}
    return {"body": body, "digest": _digest(body)}


@dataclass(frozen=True)
class Inventory:
    digest: str
    candidates: tuple[str, ...]
    rows: tuple[Sample, ...]
    page_count: int
    duplicate_page_deliveries: int


def close_pages(expected_page_ids: Iterable[str], pages: Iterable[dict],
                expected_candidates: Iterable[str], expected_events: Iterable[str]) -> Inventory:
    """Accept a complete immutable set before allowing any winner selection."""
    expected_pages = tuple(expected_page_ids)
    candidates = tuple(sorted(expected_candidates))
    events = tuple(sorted(expected_events))
    if not expected_pages or len(set(expected_pages)) != len(expected_pages):
        raise ValueError("Expected page identities must be nonempty and unique")
    if not candidates or len(set(candidates)) != len(candidates):
        raise ValueError("Expected candidate identities must be nonempty and unique")
    if not events or len(set(events)) != len(events):
        raise ValueError("Expected event identities must be nonempty and unique")
    accepted: dict[str, dict] = {}
    duplicates = 0
    for page in pages:
        body = page["body"]
        if _digest(body) != page["digest"]:
            raise ValueError("Page content changed after sealing")
        name = body["page_id"]
        if name not in expected_pages:
            raise ValueError("Unexpected page identity")
        if name in accepted:
            if accepted[name] != page:
                raise ValueError("Conflicting delivery of one page")
            duplicates += 1
            continue
        accepted[name] = page
    if set(accepted) != set(expected_pages):
        raise ValueError("Complete page closure is required before comparison")
    samples: dict[tuple[str, str], Sample] = {}
    for page in accepted.values():
        for value in page["body"]["samples"]:
            row = Sample(**value)
            row.as_dict()
            key = (row.candidate, row.event)
            if row.candidate not in candidates or row.event not in events:
                raise ValueError("Unexpected candidate or event identity")
            if key in samples:
                raise ValueError("Duplicate candidate-event result")
            samples[key] = row
    expected_keys = {(candidate, event) for candidate in candidates for event in events}
    if set(samples) != expected_keys:
        raise ValueError("Every declared candidate must cover every declared event")
    rows = tuple(samples[key] for key in sorted(samples))
    identity = {"pages": {name: accepted[name]["digest"] for name in sorted(accepted)},
                "candidates": candidates, "events": events}
    return Inventory(_digest(identity), candidates, rows, len(accepted), duplicates)


def advance_comparison(inventory: Inventory, prior: Mapping | None = None,
                       max_new_candidates: int = 1) -> dict:
    """Reduce bounded work while retaining every previously completed candidate."""
    if isinstance(max_new_candidates, bool) or not isinstance(max_new_candidates, int) or max_new_candidates < 1:
        raise ValueError("A positive integer work allowance is required")
    completed: dict[str, dict] = {}
    if prior is not None:
        if prior["inventory_digest"] != inventory.digest:
            raise ValueError("A comparison cannot resume against changed input")
        for candidate, receipt in prior["completed"].items():
            if candidate not in inventory.candidates:
                raise ValueError("Unexpected completed candidate")
            if _digest(receipt["body"]) != receipt["digest"]:
                raise ValueError("Completed comparison receipt changed")
            if receipt["body"]["candidate"] != candidate:
                raise ValueError("Completed comparison identity mismatch")
            completed[candidate] = receipt
    reused = len(completed)
    remaining = [candidate for candidate in inventory.candidates if candidate not in completed]
    for candidate in remaining[:max_new_candidates]:
        values = [row.loss for row in inventory.rows if row.candidate == candidate]
        body = {"candidate": candidate, "event_count": len(values),
                "mean_loss": math.fsum(values) / len(values)}
        completed[candidate] = {"body": body, "digest": _digest(body)}
    pending = [candidate for candidate in inventory.candidates if candidate not in completed]
    champion = None
    if not pending:
        champion = min(inventory.candidates,
                       key=lambda candidate: (completed[candidate]["body"]["mean_loss"], candidate))
    return {"inventory_digest": inventory.digest, "completed": completed,
            "new_comparisons": len(completed) - reused, "reused_comparisons": reused,
            "remaining_candidates": pending, "complete": not pending,
            "champion": champion, "real_model_fits": 0,
            "evidence_class": "INVENTED_ENGINEERING_DEMONSTRATION"}


def demo_pages() -> tuple[dict, ...]:
    return (
        seal_page("fictional-page-one", [Sample("amber", "sample-a", 1.0), Sample("amber", "sample-b", 3.0)]),
        seal_page("fictional-page-two", [Sample("birch", "sample-a", 4.0), Sample("birch", "sample-b", 6.0)]),
        seal_page("fictional-page-three", [Sample("cedar", "sample-a", 7.0), Sample("cedar", "sample-b", 9.0)]),
    )


def main() -> int:
    pages = demo_pages()
    inventory = close_pages([page["body"]["page_id"] for page in pages], pages,
                            ("amber", "birch", "cedar"), ("sample-a", "sample-b"))
    state = None
    visits = []
    for _ in range(3):
        state = advance_comparison(inventory, state, max_new_candidates=1)
        visits.append({key: state[key] for key in ("new_comparisons", "reused_comparisons",
                                                  "remaining_candidates", "champion")})
    print(json.dumps({"evidence_class": state["evidence_class"], "visits": visits,
                      "winner_from_first_page": state["champion"] == "amber",
                      "real_model_fits": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
