from dataclasses import replace
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from examples.review_lab.prospective_state import PaperLedger, fixture


class ProspectiveStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'ledger.sqlite';self.now='2030-01-02T18:50:00Z'
        self.ledger=PaperLedger(self.path,clock=lambda:self.now)

    def test_commit_is_immutable_and_reentry_reuses_hash(self):
        old=self.ledger.commit(fixture());self.now='2030-01-02T23:00:00Z'
        self.assertEqual(old,self.ledger.commit(fixture()))
        self.assertEqual(self.ledger.snapshot()['events'],1)

    def test_changed_decision_rejected(self):
        self.ledger.commit(fixture())
        with self.assertRaises(ValueError):self.ledger.commit(replace(fixture(),probability=.7))

    def test_early_decision_is_not_pretended_to_be_at_cutoff(self):
        self.now='2030-01-02T18:40:00Z'
        with self.assertRaises(ValueError):self.ledger.commit(fixture())

    def test_late_decision_rejected(self):
        self.now='2030-01-02T19:00:01Z'
        with self.assertRaises(ValueError):self.ledger.commit(fixture())

    def test_stale_and_future_native_quotes_rejected(self):
        for stamp in ('2030-01-02T18:34:59Z','2030-01-02T18:50:01Z'):
            with self.assertRaises(ValueError):self.ledger.commit(replace(fixture(),quote_at=stamp))

    def test_future_forecast_rejected(self):
        with self.assertRaises(ValueError):self.ledger.commit(replace(fixture(),forecast_at='2030-01-02T19:00:00Z'))

    def test_missing_evidence_rejected(self):
        with self.assertRaises(ValueError):self.ledger.commit(replace(fixture(),evidence_verified=('policy',)))

    def test_overbudget_transaction_preserves_previous_event(self):
        self.ledger.commit(fixture())
        with self.assertRaises(ValueError):self.ledger.commit(replace(fixture(),decision_id='b',game_id='b',stake_cents=8000))
        self.assertEqual(self.ledger.snapshot()['events'],1)

    def test_duplicate_game_different_id_rejected(self):
        self.ledger.commit(fixture())
        with self.assertRaises(ValueError):self.ledger.commit(replace(fixture(),decision_id='b'))

    def test_native_week_cannot_share_wrong_budget(self):
        self.ledger.commit(fixture())
        with self.assertRaises(ValueError):self.ledger.commit(replace(fixture(),decision_id='b',game_id='b',week=2))

    def test_fee_and_cost_must_fit_reserved_stake(self):
        with self.assertRaises(ValueError):self.ledger.commit(replace(fixture(),fee_cents=501))

    def test_pending_profit_is_not_zero(self):
        self.ledger.commit(fixture());s=self.ledger.snapshot()
        self.assertIsNone(s['complete_paper_profit_cents']);self.assertIsNone(s['actual_profit'])
        self.assertEqual(s['unsettled_exposure_cents'],2500)

    def test_settlement_is_separate_immutable_event(self):
        decision=self.ledger.commit(fixture());self.now='2030-01-02T23:00:00Z'
        self.ledger.settle(fixture().decision_id,unit_payout_cents=100,outcome_available_at=self.now,source_sha256='c'*64)
        self.assertEqual(self.ledger.snapshot()['complete_paper_profit_cents'],1960)
        self.assertEqual(self.ledger.snapshot()['unsettled_exposure_cents'],0)
        self.assertEqual(self.ledger.commit(fixture()),decision)
        with self.assertRaises(ValueError):self.ledger.settle(fixture().decision_id,unit_payout_cents=0,outcome_available_at=self.now,source_sha256='c'*64)

    def test_early_settlement_rejected(self):
        self.ledger.commit(fixture())
        with self.assertRaises(ValueError):self.ledger.settle(fixture().decision_id,unit_payout_cents=100,outcome_available_at=self.now,source_sha256='c'*64)

    def test_pre_kickoff_outcome_cannot_be_used_later(self):
        self.ledger.commit(fixture());self.now='2030-01-02T23:00:00Z'
        with self.assertRaises(ValueError):self.ledger.settle(fixture().decision_id,unit_payout_cents=100,outcome_available_at='2030-01-02T19:59:59Z',source_sha256='c'*64)

    def test_outcome_source_requires_hex_identity(self):
        self.ledger.commit(fixture());self.now='2030-01-02T23:00:00Z'
        with self.assertRaises(ValueError):self.ledger.settle(fixture().decision_id,unit_payout_cents=100,outcome_available_at=self.now,source_sha256='z'*64)

    def test_settlement_boolean_is_not_a_financial_integer(self):
        self.ledger.commit(fixture());self.now='2030-01-02T23:00:00Z'
        with self.assertRaises(ValueError):self.ledger.settle(fixture().decision_id,unit_payout_cents=False,outcome_available_at=self.now,source_sha256='c'*64)

    def test_budget_is_immutable(self):
        with sqlite3.connect(self.path) as db:
            for sql in ('DELETE FROM config','UPDATE config SET value="20000"'):
                with self.assertRaises(sqlite3.IntegrityError):db.execute(sql)

    def test_sql_updates_and_deletes_are_blocked(self):
        self.ledger.commit(fixture())
        with sqlite3.connect(self.path) as db:
            for sql in ('DELETE FROM events','UPDATE events SET event_hash="bad"'):
                with self.assertRaises(sqlite3.IntegrityError):db.execute(sql)

    def test_resume_rejects_budget_change(self):
        with self.assertRaises(ValueError):PaperLedger(self.path,clock=lambda:self.now,budget_cents=20000)

    def test_chain_detects_tampering_even_if_trigger_removed(self):
        self.ledger.commit(fixture())
        with sqlite3.connect(self.path)as db:
            db.execute('DROP TRIGGER immutable_event_update');db.execute('UPDATE events SET event_hash="bad"')
        with self.assertRaises(ValueError):self.ledger.snapshot()

    def test_invalid_probability_rejected(self):
        for p in (float('nan'),float('inf'),0,1):
            with self.assertRaises(ValueError):self.ledger.commit(replace(fixture(),probability=p))


if __name__=='__main__':unittest.main()
