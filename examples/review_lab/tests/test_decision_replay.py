import copy
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
from pathlib import Path
import tempfile
import unittest

from examples.review_lab.decision_replay import Candidate,Rule,freeze_decision,save_ledger,settle,verify_ledger


class DecisionReplayTests(unittest.TestCase):
    def setUp(self):
        self.lock=datetime(2021,10,5,12,tzinfo=timezone.utc)
        self.rule=Rule('invented',2021,4,self.lock-timedelta(days=2),self.lock,D('100'),2,D('.02'),timedelta(minutes=10))
        self.a=Candidate('a','invented',2021,4,self.lock+timedelta(days=1),self.lock-timedelta(hours=1),
                         self.lock-timedelta(days=3),self.lock-timedelta(days=2),self.lock-timedelta(minutes=2),D('.60'),D('.50'),D('.01'),50,True)
        self.b=replace(self.a,event_id='b',unit_payoff_probability=D('.48'))

    def freeze(self,candidates=None,expected=None,rule=None,decided=None):
        return freeze_decision(rule or self.rule,(self.a,self.b)if candidates is None else candidates,
            frozenset(('a','b'))if expected is None else expected,decided_at=self.lock if decided is None else decided)

    def test_cost_depth_fees_and_unspent_cash(self):
        ledger=self.freeze();p=ledger['positions'][0]
        self.assertEqual(p['contracts'],50);self.assertEqual(D(p['fees']),D('.50'))
        self.assertEqual(D(ledger['total_cost']),D('25.50'));self.assertEqual(D(ledger['unspent_cash']),D('74.50'))
        self.assertFalse(p['observed_fill']);self.assertFalse(ledger['outcomes_used_in_selection'])

    def test_missing_or_duplicate_universe_rejected(self):
        for candidates in ((self.a,),(self.a,self.a)):
            with self.assertRaises(ValueError):self.freeze(candidates)

    def test_native_week_and_league_enforced(self):
        for change in ({'week':5},{'league':'different'},{'season':2020},{'week':True}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.freeze((self.a,replace(self.b,**change)))

    def test_decision_after_lock_rejected(self):
        with self.assertRaises(ValueError):self.freeze(decided=self.lock+timedelta(seconds=1))

    def test_policy_created_after_decision_rejected(self):
        with self.assertRaises(ValueError):self.freeze(rule=replace(self.rule,frozen_at=self.lock+timedelta(seconds=1)))

    def test_unavailable_model_or_features_excluded(self):
        for field in ('model_available_at','features_available_at'):
            bad=replace(self.a,**{field:self.a.forecast_at+timedelta(seconds=1)})
            ledger=self.freeze((bad,self.b));self.assertFalse(ledger['positions'])
            self.assertIn('UNAVAILABLE_FORECAST_DEPENDENCY',ledger['rejected'][0]['reasons'])

    def test_forecast_after_decision_excluded(self):
        ledger=self.freeze((replace(self.a,forecast_at=self.lock+timedelta(seconds=1)),self.b))
        self.assertFalse(ledger['positions'])

    def test_started_event_excluded(self):
        ledger=self.freeze((replace(self.a,kickoff=self.lock),self.b));self.assertFalse(ledger['positions'])

    def test_stale_future_and_unverified_quotes_excluded(self):
        for change in ({'quote_at':self.lock-timedelta(minutes=11)},{'quote_at':self.lock+timedelta(seconds=1)},
                       {'quote_timestamp_verified':False}):
            self.assertFalse(self.freeze((replace(self.a,**change),self.b))['positions'])

    def test_quote_freshness_uses_actual_decision_clock(self):
        ledger=self.freeze((replace(self.a,quote_at=self.lock-timedelta(minutes=1)),self.b),decided=self.lock-timedelta(minutes=2))
        self.assertFalse(ledger['positions'])

    def test_invalid_amount_probability_or_depth_rejected(self):
        for change in ({'ask':D(0)},{'ask':D(1)},{'ask':D('NaN')},{'ask':.5},
                       {'unit_payoff_probability':D('1.1')},{'fee_per_contract':D('-.1')},{'displayed_depth':True}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.freeze((replace(self.a,**change),self.b))

    def test_zero_depth_and_insufficient_edge_leave_cash(self):
        self.assertEqual(D(self.freeze((replace(self.a,displayed_depth=0),self.b))['unspent_cash']),D(100))

    def test_position_cap_and_tie_break_are_predeclared(self):
        b=replace(self.a,event_id='b')
        first=self.freeze((b,self.a),rule=replace(self.rule,maximum_positions=1))
        second=self.freeze((self.a,b),rule=replace(self.rule,maximum_positions=1))
        self.assertEqual(first,second);self.assertEqual(first['positions'][0]['event_id'],'a')
        self.assertIn('POSITION_CAP',first['rejected'][0]['reasons'])

    def test_budget_includes_fees_and_integer_contracts(self):
        ledger=self.freeze((replace(self.a,displayed_depth=1000),self.b))
        self.assertEqual(ledger['positions'][0]['contracts'],98)
        self.assertLessEqual(D(ledger['total_cost']),D(50))

    def test_too_small_slot_does_not_force_a_position(self):
        ledger=self.freeze(rule=replace(self.rule,budget=D('.10')))
        self.assertFalse(ledger['positions']);self.assertEqual(D(ledger['unspent_cash']),D('.10'))

    def test_unknown_outcomes_do_not_become_zero_profit(self):
        result=settle(self.freeze(),{})
        self.assertIsNone(result['complete_portfolio_profit']);self.assertIsNone(result['complete_portfolio_roi'])
        self.assertEqual(result['pending'],['a'])

    def test_settlement_does_not_change_selection(self):
        ledger=self.freeze();before=copy.deepcopy(ledger)
        win=settle(ledger,{'a':D(1)});loss=settle(ledger,{'a':D(0)})
        self.assertEqual(D(win['complete_portfolio_profit']),D('24.50'))
        self.assertEqual(D(loss['complete_portfolio_profit']),D('-25.50'));self.assertEqual(ledger,before)

    def test_partial_settlement_keeps_portfolio_unknown(self):
        ledger=self.freeze((self.a,replace(self.a,event_id='b')))
        result=settle(ledger,{'a':D(1)})
        self.assertIsNone(result['complete_portfolio_profit']);self.assertEqual(result['pending'],['b'])

    def test_unselected_settlement_or_invalid_payoff_rejected(self):
        for outcome in ({'x':D(1)},{'a':D(2)},{'a':1.0}):
            with self.subTest(outcome=outcome),self.assertRaises(ValueError):settle(self.freeze(),outcome)

    def test_tampered_ledger_rejected(self):
        ledger=self.freeze();ledger['positions'][0]['contracts']=500
        with self.assertRaises(ValueError):verify_ledger(ledger)
        with self.assertRaises(ValueError):settle(ledger,{'a':D(1)})

    def test_saved_selection_allows_exact_reentry_not_overwrite(self):
        with tempfile.TemporaryDirectory()as folder:
            path=Path(folder)/'selection.json';ledger=self.freeze();save_ledger(ledger,path);before=path.read_bytes()
            save_ledger(ledger,path);self.assertEqual(path.read_bytes(),before)
            changed=self.freeze(rule=replace(self.rule,budget=D(200)))
            with self.assertRaises(ValueError):save_ledger(changed,path)
            self.assertEqual(path.read_bytes(),before)

    def test_rule_and_naive_clock_domains_rejected(self):
        for change in ({'maximum_positions':0},{'budget':D(-1)},{'maximum_quote_age':timedelta(seconds=-1)},
                       {'lock_at':self.lock.replace(tzinfo=None)},{'week':True}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.freeze(rule=replace(self.rule,**change))


if __name__=='__main__':unittest.main()
