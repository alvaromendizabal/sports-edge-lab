"""An executable, credential-free walkthrough of invented basketball evidence."""
from __future__ import annotations

import argparse
from datetime import timedelta
import hashlib
import json
from pathlib import Path

from .contracts import Game, Identity, League, QuoteEvidence, ScoredForecast, SelectionPolicy, SourceEvidence, matched_brier, utc


def walkthrough():
    reports = []
    policy = SelectionPolicy()
    policy.validate_fold((2022, 2023, 2024), 2025)
    policy.validate_fold((2022, 2023, 2024, 2025), 2026)
    try:
        policy.validate_selection((2025, 2026, 2027))
    except ValueError:
        protected_season_rejected = True
    else:
        protected_season_rejected = False
    for league in League:
        game = Game(Identity(league, "synthetic", "event", "game-1"),
                    Identity(league, "synthetic", "team", "team-a"),
                    Identity(league, "synthetic", "team", "team-b"),
                    utc("2026-02-01T20:00:00Z"), 2025, 2026, "regular", None)
        cutoff = game.cutoff(60)
        evidence = SourceEvidence(hashlib.sha256(b"invented public fixture").hexdigest(),
                                  utc("2026-02-02T00:00:00Z"),
                                  utc("2026-02-01T18:00:00Z"), None, None)
        tier_unknown = evidence.evidence_tier(cutoff)
        tier_assumed = evidence.evidence_tier(cutoff, assumed_available_at=utc("2026-02-01T18:00:00Z"))
        early = QuoteEvidence(game.event, cutoff, cutoff - timedelta(minutes=1), cutoff - timedelta(minutes=2), utc("2026-02-02T00:00:00Z"))
        stale = QuoteEvidence(game.event, cutoff, cutoff - timedelta(minutes=1), cutoff - timedelta(minutes=30), utc("2026-02-02T00:00:00Z"))
        later = QuoteEvidence(game.event, cutoff, cutoff + timedelta(minutes=1), cutoff + timedelta(minutes=1), utc("2026-02-02T00:00:00Z"))
        # Both probability values and the outcome below are invented inputs.
        # There is no estimator, basketball dataset or fitted coefficient here.
        scores = matched_brier([ScoredForecast(game.event, cutoff, .60, 1)],
                              [ScoredForecast(game.event, cutoff, .55, 1)])
        reports.append({"league": league.value, "event_identity": str(game.event),
                        "unknown_publication_tier": tier_unknown, "explicit_assumption_tier": tier_assumed,
                        "eligible_archived_quote": early.eligible(), "stale_quote_rejected": not stale.eligible(),
                        "later_quote_rejected": not later.eligible(), "neutral_status": game.neutral,
                        "invented_score_demonstration": scores})
    return {"schema": "sports-edge-public-basketball-contracts-v1", "synthetic_only": True,
            "source": "invented fixtures written in this public module", "model_fits": 0,
            "real_basketball_metrics": None, "owner_execution_status": "B003_completed_reconstructed_research",
            "previous_owner_execution_status": "B001_failed_before_modeling",
            "next_release": "B004", "next_owner_execution_status": "pending",
            "owner_real_model_fits": 60, "owner_cumulative_real_model_fits": 232, "owner_imported_predecessor_units": 156, "owner_real_forecast_rows": 110,
            "owner_distinct_forecast_games": 61, "owner_forecast_kind": "early_outlook_before_declared_horizon",
            "owner_qualified_current_market_probabilities": 0, "owner_profit": None,
            "owner_aggregate_evidence": "docs/evidence/2026-10-27-basketball-b003.json",
            "example_metrics_are_not_owner_metrics": True,
            "network_calls": 0, "paid_requests": 0, "orders": 0,
            "protected_2027_selection_rejected": protected_season_rejected,
            "historical_validation_seasons": list(policy.historical_validation_seasons),
            "reports": reports}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the synthetic JSON report")
    args = parser.parse_args()
    report = walkthrough()
    encoded = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
        saved = json.loads(args.output.read_text())
        if saved != report:
            raise ValueError("Saved synthetic report does not match its source")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
