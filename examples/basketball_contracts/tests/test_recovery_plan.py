"""Invented fixtures prove ingestion, scope, chronology and spending invariants."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from examples.basketball_contracts.recovery_plan import (
    Budget, Capability, Catalog, Need, Quota, QuotaJournal, SCHEMA,
    SnapshotRequest, digest, encoded, plan_recovery, walkthrough,
)
NOW = "2026-10-28T20:00:00Z"
CUT = "2025-01-01T19:00:00Z"
PIN = digest({"invented_receipt": True})


def need(n=1, **changes):
    return replace(Need("nba", f"fixture-event-{n}", f"fixture-provider-{n}", f"fixture-home-{n}", f"fixture-away-{n}",
        "2025-01-01T20:00:00Z", CUT, PIN), **changes)


def request(**changes):
    return replace(SnapshotRequest("basketball_nba", CUT, ("h2h",), ("us",)), **changes)


def observation(n=1, **changes):
    result = {"event_id": f"fixture-provider-{n}", "home_id": f"fixture-home-{n}", "away_id": f"fixture-away-{n}",
        "tipoff": "2025-01-01T20:00:00Z", "bookmaker_id": "fixture-book", "market": "h2h", "region": "us",
        "quote_updated_at": "2025-01-01T18:55:00Z", "outcomes": [
            {"side": "home", "decimal_price": 1.9}, {"side": "away", "decimal_price": 1.95}]}
    result.update(changes); return result


def raw(rows=None, **changes):
    result = {"schema": SCHEMA, "sport_key": "basketball_nba", "snapshot_at": CUT,
        "records": [observation()] if rows is None else rows}
    result.update(changes); return encoded(result)


def add(catalog, payload=None, req=None, alias="fixture-location", stamp=NOW):
    payload = raw() if payload is None else payload
    catalog.add(alias, payload, hashlib.sha256(payload).hexdigest(), req or request(), stamp)
    return catalog


def sealed(rows=None, **changes):
    catalog = Catalog()
    if rows is not None: add(catalog, raw(rows, **changes))
    catalog.seal(PIN)
    return catalog


def capability(**changes):
    return replace(Capability("basketball_nba", "2020-07-01T00:00:00Z", ("h2h", "spreads", "totals"), ("us", "eu"),
        True, "2026-10-28T19:59:00Z", "2026-10-28T21:00:00Z", PIN), **changes)


def budget(**changes): return replace(Budget(20, 0, 1000, 0, PIN), **changes)
def quota(**changes): return replace(Quota(1000, NOW, PIN), **changes)


def plan(needs=None, catalog=None, **changes):
    params = {"needs": needs or [need()], "catalog": catalog or sealed(), "capabilities": [capability()],
        "budget": budget(), "quota": quota(), "now": NOW}
    params.update(changes); return plan_recovery(**params)


class CatalogContracts(unittest.TestCase):
    def test_hash_identity_deduplicates_bytes_but_preserves_retrievals(self):
        cat = add(Catalog()); add(cat, alias="fixture-second-location")
        self.assertEqual(cat.summary()["content_objects"], 1)
        self.assertEqual(cat.summary()["retrieval_receipts"], 2)
        self.assertEqual(cat.summary()["normalized_observations"], 1)

    def test_same_alias_retains_new_content_version(self):
        cat = add(Catalog()); add(cat, raw([observation(2)]))
        self.assertEqual(cat.summary()["content_objects"], 2)
        self.assertEqual(cat.summary()["aliases"], 1)

    def test_exact_receipt_reentry_is_idempotent(self):
        cat = add(Catalog()); add(cat)
        self.assertEqual(cat.summary()["retrieval_receipts"], 1)

    def test_hash_mismatch_prevents_indexing(self):
        cat = Catalog()
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            cat.add("fixture-alias", raw(), "0" * 64, request(), NOW)
        self.assertEqual(cat.summary()["content_objects"], 0)

    def test_unclassified_objects_prevent_gap_plan(self):
        cat = Catalog()
        with self.assertRaisesRegex(ValueError, "unclassified"): cat.seal(PIN, unresolved_objects=1)
        with self.assertRaisesRegex(ValueError, "seal"): plan(catalog=cat)

    def test_sealed_inventory_cannot_be_mutated(self):
        with self.assertRaisesRegex(ValueError, "immutable"): add(sealed())

    def test_wrong_sport_does_not_enter_catalog(self):
        with self.assertRaisesRegex(ValueError, "sport"): add(Catalog(), raw(sport_key="basketball_wncaab"))

    def test_after_request_snapshot_rejected(self):
        with self.assertRaisesRegex(ValueError, "snapshot"): add(Catalog(), raw(snapshot_at="2025-01-01T19:01:00Z"))

    def test_retrieval_before_snapshot_rejected(self):
        with self.assertRaisesRegex(ValueError, "snapshot"): add(Catalog(), stamp="2025-01-01T18:00:00Z")

    def test_quote_after_snapshot_rejected(self):
        with self.assertRaisesRegex(ValueError, "quote update"):
            add(Catalog(), raw([observation(quote_updated_at="2025-01-01T19:01:00Z")]))

    def test_duplicate_market_observation_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"): add(Catalog(), raw([observation(), observation()]))

    def test_malformed_market_pairs_rejected(self):
        for outcomes in ([{"side": "home", "decimal_price": 1.9}],
                         [{"side": "home", "decimal_price": 1.9}, {"side": "home", "decimal_price": 2.1}],
                         [{"side": "home", "decimal_price": 1.0}, {"side": "away", "decimal_price": 2.1}]):
            with self.subTest(outcomes=outcomes), self.assertRaises(ValueError):
                add(Catalog(), raw([observation(outcomes=outcomes)]))

    def test_spread_lines_must_be_opposing(self):
        quote = observation(market="spreads", outcomes=[{"side": "home", "decimal_price": 1.9, "line": -3},
            {"side": "away", "decimal_price": 1.9, "line": 4}])
        with self.assertRaisesRegex(ValueError, "opposing"):
            add(Catalog(), raw([quote]), request(markets=("spreads",)))

    def test_total_lines_must_agree(self):
        quote = observation(market="totals", outcomes=[{"side": "over", "decimal_price": 1.9, "line": 210},
            {"side": "under", "decimal_price": 1.9, "line": 211}])
        with self.assertRaisesRegex(ValueError, "totals"):
            add(Catalog(), raw([quote]), request(markets=("totals",)))

    def test_secret_url_is_not_a_location_alias(self):
        with self.assertRaisesRegex(ValueError, "credentials"): add(Catalog(), alias="https://example.invalid/?apiKey=fixture")


class PlanningContracts(unittest.TestCase):
    def test_cached_quote_needs_no_quota_or_new_authorization(self):
        p = plan(catalog=sealed([observation()]), capabilities=[], quota=None, budget=budget(authorization_sha256=None))
        self.assertEqual((p["covered_cells"], p["planned_requests"]), (1, 0))
        self.assertEqual(p["blocked_by"], []); self.assertFalse(p["network_dispatch_implemented"])

    def test_multiple_games_share_one_snapshot_request(self):
        p = plan([need(1), need(2), need(3)])
        self.assertEqual((p["expected_cells"], p["planned_requests"], p["planned_credit_ceiling"]), (3, 1, 10))

    def test_identical_and_overlapping_needs_do_not_inflate_cells(self):
        p = plan([need(), need(), need(markets=("h2h", "totals"))])
        self.assertEqual((p["input_needs"], p["expected_cells"]), (3, 2)); self.assertEqual(p["planned_credit_ceiling"], 20)

    def test_mismatched_canonical_identity_cannot_reuse_quote(self):
        for change in ({"provider_event_id": "fixture-other"}, {"home_id": "fixture-other"}, {"tipoff": "2025-01-01T20:05:00Z"}):
            with self.subTest(change=change):
                p = plan([need(**change)], sealed([observation()]))
                self.assertEqual(p["covered_cells"], 0); self.assertEqual(p["planned_requests"], 0)
                self.assertIn("already_captured", p["deferred"][0]["reason"])

    def test_ambiguous_binding_across_market_sets_rejected(self):
        with self.assertRaisesRegex(ValueError, "conflicting event binding"):
            plan([need(), need(home_id="fixture-other", markets=("totals",))])

    def test_cutoff_after_tipoff_rejected(self):
        with self.assertRaisesRegex(ValueError, "pregame"): need(cutoff="2025-01-01T20:00:00Z")

    def test_unknown_timezone_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone"): need(cutoff="2025-01-01T19:00:00")

    def test_freshness_boundary_is_inclusive_and_stale_not_relabelled(self):
        self.assertEqual(plan(catalog=sealed([observation(quote_updated_at="2025-01-01T18:45:00Z")]))["covered_cells"], 1)
        p = plan(catalog=sealed([observation(quote_updated_at="2025-01-01T18:44:59Z")]))
        self.assertEqual((p["covered_cells"], p["planned_requests"], len(p["deferred"])), (0, 0, 1))

    def test_archived_observation_is_not_prospective_capture(self):
        p = plan(catalog=sealed([observation()]))
        self.assertEqual(p["cells"][0]["observations"][0]["evidence_tier"], "provider_historical_archive_not_prospective_capture")

    def test_empty_exact_response_does_not_trigger_endless_retries(self):
        p = plan(catalog=sealed([]))
        self.assertEqual((p["covered_cells"], p["planned_requests"], len(p["deferred"])), (0, 0, 1))

    def test_prior_broader_request_prevents_redundant_subset(self):
        cat = add(Catalog(), raw([]), request(markets=("h2h", "totals"), regions=("us", "eu"))); cat.seal(PIN)
        self.assertEqual(plan(catalog=cat)["planned_requests"], 0)

    def test_cache_different_snapshot_can_still_supply_fresh_quote(self):
        cat = add(Catalog(), raw(snapshot_at="2025-01-01T18:55:00Z"), request(at="2025-01-01T18:56:00Z")); cat.seal(PIN)
        self.assertEqual(plan(catalog=cat)["covered_cells"], 1)

    def test_capability_failures_are_deferred(self):
        for cap in (capability(entitlement_confirmed=False), capability(historical_from="2025-02-01T00:00:00Z"),
                    capability(valid_until=NOW), capability(sport_key="basketball_wncaab")):
            with self.subTest(cap=cap):
                p = plan(capabilities=[cap]); self.assertEqual((p["planned_requests"], len(p["deferred"])), (0, 1))

    def test_unknown_quota_prevents_dispatch(self):
        p = plan(quota=None)
        self.assertIn("fresh_verified_provider_remaining_quota_missing", p["blocked_by"])
        self.assertFalse(p["dispatch_permitted_by_example_contract"])

    def test_stale_and_future_quota_prevent_dispatch(self):
        for at in ("2026-10-28T19:54:59Z", "2026-10-28T20:00:01Z"):
            with self.subTest(at=at): self.assertFalse(plan(quota=quota(observed_at=at))["dispatch_permitted_by_example_contract"])

    def test_project_and_provider_credit_caps_are_independent(self):
        self.assertIn("cumulative_credit_ceiling", plan(budget=budget(credit_limit=9))["blocked_by"])
        self.assertIn("provider_credit_allowance", plan(quota=quota(remaining_credits=9))["blocked_by"])

    def test_request_ceiling_counts_even_zero_credit_discoveries(self):
        self.assertIn("cumulative_request_ceiling", plan(budget=budget(requests_used=20))["blocked_by"])

    def test_incremental_permission_is_not_inferred_from_subscription(self):
        self.assertIn("explicit_incremental_request_and_credit_authorization_missing", plan(budget=budget(authorization_sha256=None))["blocked_by"])

    def test_cost_arithmetic_uses_unique_explicit_scopes(self):
        self.assertEqual(request(markets=("h2h", "totals", "spreads"), regions=("us", "eu")).credit_ceiling, 60)
        with self.assertRaises(ValueError): request(markets=("h2h", "h2h"))
        with self.assertRaises(ValueError): request(markets=("player_points",))

    def test_numeric_boolean_and_reset_budgets_rejected(self):
        for change in ({"request_limit": True}, {"credit_limit": -1}, {"requests_used": 21}):
            with self.subTest(change=change), self.assertRaises(ValueError): budget(**change)

    def test_plan_is_order_invariant_and_contains_no_credentials(self):
        left, right = plan([need(1), need(2)]), plan([need(2), need(1)])
        self.assertEqual(left["plan_sha256"], right["plan_sha256"]); self.assertNotIn("apiKey", json.dumps(left))

    def test_header_parser_rejects_missing_fractional_and_negative(self):
        self.assertEqual(Quota.from_headers({"X-Requests-Remaining": "123"}, NOW, PIN).remaining_credits, 123)
        for value in (None, "1.2", "-1", True):
            with self.subTest(value=value), self.assertRaises(ValueError): Quota.from_headers({"x-requests-remaining": value}, NOW, PIN)


class JournalContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "fixture-journal.jsonl"
        self.budget = budget(); self.journal = QuotaJournal(self.path, self.budget)

    def reserve(self, name="fixture-attempt-1", **changes):
        return self.journal.reserve(name, request(), quota(**changes), NOW)

    def complete(self, name="fixture-attempt-1", credits=10, stamp=NOW):
        return self.journal.complete(name, credits, PIN, stamp)

    def test_concurrent_workers_cannot_overrun_cumulative_limit(self):
        journal = QuotaJournal(Path(self.tmp.name) / "concurrent.jsonl", budget(request_limit=4))
        def reserve_one(index):
            try:
                return journal.reserve(f"fixture-worker-{index}", request(), quota(), NOW)["new_reservation"]
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            accepted = list(pool.map(reserve_one, range(12)))
        self.assertEqual(sum(accepted), 4)
        self.assertEqual(journal.state()["requests_used"], 4)

    def test_concurrent_same_attempt_is_reserved_once(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.reserve(), range(12)))
        self.assertEqual(sum(r["new_reservation"] for r in results), 1)
        self.assertEqual(self.journal.state()["requests_used"], 1)

    def test_pending_reservation_survives_restart(self):
        self.reserve(); s = QuotaJournal(self.path, self.budget).state()
        self.assertEqual((s["requests_used"], s["credits_charged_or_reserved"], s["pending_attempts"]), (1, 10, 1))

    def test_attempt_reentry_never_reserves_twice(self):
        self.assertTrue(self.reserve()["new_reservation"]); self.assertFalse(self.reserve()["new_reservation"])
        self.assertEqual(self.journal.state()["requests_used"], 1)

    def test_changed_request_cannot_reuse_attempt_identity(self):
        self.reserve()
        with self.assertRaisesRegex(ValueError, "different request"):
            self.journal.reserve("fixture-attempt-1", request(at="2025-01-01T19:01:00Z"), quota(), NOW)

    def test_complete_is_immutable_idempotent(self):
        self.reserve(); self.complete(); self.assertFalse(self.complete()["new_receipt"])
        with self.assertRaisesRegex(ValueError, "immutable"): self.complete(credits=0)

    def test_completed_empty_response_refunds_credits_not_request(self):
        self.reserve(); self.complete(credits=0); s = self.journal.state()
        self.assertEqual((s["requests_used"], s["credits_charged_or_reserved"]), (1, 0))

    def test_retry_is_a_new_attempt_with_a_new_reservation(self):
        self.reserve(); self.reserve("fixture-attempt-2")
        self.assertEqual(self.journal.state()["credits_charged_or_reserved"], 20)

    def test_pending_attempts_reduce_provider_headroom(self):
        self.reserve(remaining_credits=10)
        with self.assertRaisesRegex(ValueError, "provider quota"): self.reserve("fixture-attempt-2", remaining_credits=10)

    def test_reusing_pre_response_quota_does_not_refund_completed_spend(self):
        self.reserve(remaining_credits=10); self.complete()
        with self.assertRaisesRegex(ValueError, "provider quota"): self.reserve("fixture-attempt-2", remaining_credits=10)

    def test_later_quota_observation_accounts_for_completed_spend(self):
        self.journal.reserve("fixture-attempt-1", request(), quota(observed_at="2026-10-28T19:59:58Z"), "2026-10-28T19:59:58Z")
        self.complete(stamp="2026-10-28T19:59:59Z")
        self.assertTrue(self.reserve("fixture-attempt-2", remaining_credits=10)["new_reservation"])

    def test_completion_cannot_fabricate_pre_reservation_quota_accounting(self):
        self.reserve()
        with self.assertRaisesRegex(ValueError, "precedes reservation"):
            self.complete(stamp="2026-10-28T19:59:59Z")
        self.assertEqual(self.journal.state()["pending_attempts"], 1)

    def test_cumulative_request_budget_blocks_retry(self):
        j = QuotaJournal(Path(self.tmp.name) / "one-request.jsonl", budget(request_limit=1))
        j.reserve("fixture-a", request(), quota(), NOW); j.complete("fixture-a", 0, PIN, NOW)
        with self.assertRaisesRegex(ValueError, "cumulative"): j.reserve("fixture-b", request(), quota(), NOW)

    def test_resumed_journal_rejects_changed_budget(self):
        self.reserve()
        with self.assertRaisesRegex(ValueError, "budget identity"): QuotaJournal(self.path, budget(request_limit=21)).state()

    def test_missing_response_cannot_be_completed_without_reservation(self):
        with self.assertRaisesRegex(ValueError, "reservation"): self.complete()

    def test_unexpected_actual_charge_is_preserved_and_freezes_dispatch(self):
        self.reserve(); self.assertTrue(self.complete(credits=12)["unexpected_cost"])
        self.assertEqual(self.journal.state()["credits_charged_or_reserved"], 12)
        with self.assertRaisesRegex(ValueError, "exceeded contract"): self.reserve("fixture-next")

    def test_corrupted_or_truncated_journal_fails_closed(self):
        self.reserve(); original = self.path.read_text(); self.path.write_text(original[:-1])
        with self.assertRaisesRegex(ValueError, "incomplete"): self.journal.state()
        self.path.write_text(original.replace('"credit_ceiling":10', '"credit_ceiling":11'))
        with self.assertRaisesRegex(ValueError, "chain mismatch"): self.journal.state()

    def test_quota_unknown_or_stale_fails_before_reservation(self):
        for q in (None, quota(observed_at="2026-10-28T19:00:00Z")):
            with self.subTest(q=q), self.assertRaisesRegex(ValueError, "fresh"):
                self.journal.reserve("fixture-a", request(), q, NOW)
        self.assertEqual(self.journal.state()["requests_used"], 0)


class WalkthroughContracts(unittest.TestCase):
    def test_documented_walkthrough_is_actual_executable_behavior(self):
        value = walkthrough(); p = value["plan"]
        self.assertTrue(value["synthetic"])
        self.assertEqual((p["inventory"]["content_objects"], p["inventory"]["retrieval_receipts"]), (1, 2))
        self.assertEqual((p["covered_cells"], p["expected_cells"], p["planned_requests"], p["planned_credit_ceiling"]), (2, 6, 1, 20))
        self.assertEqual((value["actual_requests"], value["actual_fits"], value["real_records_recovered"]), (0, 0, 0))


if __name__ == "__main__": unittest.main()
