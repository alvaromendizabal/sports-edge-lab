import copy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from examples.review_lab.decision_replay import demonstration
from examples.review_lab.portfolio_evidence import Commitment,commit,settle_committed,compare_venue_alternatives


class PortfolioEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'selection.json';self.ledger=demonstration()['ledger']
        self.commitment=commit(self.ledger,self.path,'ARCHIVED_ASK_DEPTH_FEES')

    def test_hash_is_integrity_not_historical_timestamp_attestation(self):
        result=settle_committed(self.path,self.commitment,{'a':Decimal(1)})
        self.assertEqual(result['simulated_profit'],'24.50')
        self.assertFalse(result['historical_existence_proved_by_local_hash'])
        self.assertIsNone(result['actual_profit']);self.assertFalse(result['actual_executed_wagers'])

    def test_display_price_never_fabricates_profit(self):
        for evidence in ('UNAVAILABLE','DISPLAY_ONLY'):
            path=Path(self.tmp.name)/(evidence+'.json');committed=commit(self.ledger,path,evidence)
            result=settle_committed(path,committed,{'a':Decimal(1)})
            self.assertIsNone(result['simulated_profit']);self.assertIsNone(result['simulated_roi'])

    def test_unsettled_outcomes_remain_unknown(self):
        result=settle_committed(self.path,self.commitment,{})
        self.assertIsNone(result['simulated_profit']);self.assertEqual(result['pending'],['a'])

    def test_missing_commitment_is_not_created_by_settlement(self):
        self.path.unlink()
        with self.assertRaises(FileNotFoundError):settle_committed(self.path,self.commitment,{'a':Decimal(1)})

    def test_outcome_change_does_not_change_committed_selection(self):
        before=self.path.read_bytes()
        win=settle_committed(self.path,self.commitment,{'a':Decimal(1)})
        loss=settle_committed(self.path,self.commitment,{'a':Decimal(0)})
        self.assertEqual(win['selection_sha256'],loss['selection_sha256'])
        self.assertEqual(self.path.read_bytes(),before)

    def test_changed_bytes_rejected_before_outcomes(self):
        self.path.write_bytes(self.path.read_bytes()+b' ')
        with self.assertRaises(ValueError):settle_committed(self.path,self.commitment,{'a':Decimal(1)})

    def test_rebound_selection_identity_rejected(self):
        with self.assertRaises(ValueError):settle_committed(self.path,replace(self.commitment,selection_sha256='0'*64),{'a':Decimal(1)})

    def test_actual_execution_claim_rejected(self):
        with self.assertRaises(ValueError):commit(self.ledger,self.path,'ACTUAL_EXECUTION')
        with self.assertRaises(ValueError):settle_committed(self.path,replace(self.commitment,evidence_class='ACTUAL_EXECUTION'),{})

    def test_evidence_class_cannot_change_under_old_commitment(self):
        with self.assertRaises(ValueError):settle_committed(self.path,replace(self.commitment,evidence_class='DISPLAY_ONLY'),{'a':Decimal(1)})

    def test_three_alternatives_count_capital_once(self):
        result=compare_venue_alternatives({'a':self.ledger,'b':self.ledger,'best':self.ledger})
        self.assertEqual(result['capital_allocated_once'],'100')
        self.assertEqual(len(result['alternatives']),3);self.assertTrue(result['scenario_profits_must_not_be_added'])

    def test_tampered_venue_rule_rejected(self):
        changed=copy.deepcopy(self.ledger);changed['rule']['week']+=1
        with self.assertRaises(ValueError):compare_venue_alternatives({'a':self.ledger,'b':changed})

    def test_empty_venue_universe_rejected(self):
        with self.assertRaises(ValueError):compare_venue_alternatives({})

    def test_reentry_preserves_saved_bytes(self):
        before=self.path.read_bytes();same=commit(self.ledger,self.path,'ARCHIVED_ASK_DEPTH_FEES')
        self.assertEqual(same,self.commitment);self.assertEqual(self.path.read_bytes(),before)


if __name__=='__main__':unittest.main()
