import copy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from examples.review_lab.historical_selection import (
    HistoricalScore, SelectionContract, demonstration, monitor_frozen_selection, select_historical,
)


class HistoricalSelectionTests(unittest.TestCase):
    def setUp(self):
        self.clock=datetime(2026,2,1,tzinfo=timezone.utc)
        self.contract=SelectionContract(('MARKET','a'),(2024,2025),2026,'annual',self.clock)
        self.rows=tuple(HistoricalScore(c,s,'annual',f'cohort-{s}',100,
            .6 if c=='MARKET'else .55,.2 if c=='MARKET'else .18,
            0 if c=='MARKET'else -.01,self.clock,s-1)
            for c in self.contract.candidates for s in self.contract.historical_seasons)

    def select(self,rows=None,contract=None):
        return select_historical(contract or self.contract,self.rows if rows is None else rows)

    def test_historical_selection_ignores_forward_leader(self):
        result=demonstration()
        self.assertEqual(result['selection']['selected'],'stable')
        self.assertEqual(result['monitoring']['selected'],'stable')
        self.assertFalse(result['monitoring']['ranked_by_forward_outcome'])

    def test_forward_outcomes_cannot_enter_selection(self):
        with self.assertRaisesRegex(ValueError,'forward'):
            self.select(self.rows+(replace(self.rows[-1],season=2026),))

    def test_exact_complete_cohorts_are_required(self):
        for rows in (self.rows[:-1],self.rows+(self.rows[-1],),
                     self.rows[:-1]+(replace(self.rows[-1],cohort='different'),),
                     self.rows[:-1]+(replace(self.rows[-1],games=99),)):
            with self.subTest(rows=rows),self.assertRaises(ValueError):self.select(rows)

    def test_mixed_protocols_rejected(self):
        with self.assertRaises(ValueError):self.select(self.rows[:-1]+(replace(self.rows[-1],protocol='fixed'),))

    def test_unavailable_labels_rejected(self):
        with self.assertRaisesRegex(ValueError,'unavailable'):
            self.select(self.rows[:-1]+(replace(self.rows[-1],labels_available_at=self.clock+timedelta(seconds=1)),))

    def test_training_cannot_include_evaluation_season(self):
        with self.assertRaises(ValueError):self.select(self.rows[:-1]+(replace(self.rows[-1],training_last_season=2025),))

    def test_invalid_metrics_rejected(self):
        for value in (float('nan'),float('inf'),-.1,True):
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.select(self.rows[:-1]+(replace(self.rows[-1],log_loss=value),))
        with self.assertRaises(ValueError):self.select(self.rows[:-1]+(replace(self.rows[-1],brier=1.1),))

    def test_instability_returns_market(self):
        result=self.select(self.rows[:-1]+(replace(self.rows[-1],log_loss=.65),))
        self.assertEqual(result['selected'],'MARKET')

    def test_uncertainty_or_brier_regression_blocks_candidate(self):
        for change in ({'paired_log_loss_upper':.01},{'brier':.21}):
            result=self.select(self.rows[:-1]+(replace(self.rows[-1],**change),))
            self.assertEqual(result['selected'],'MARKET')

    def test_row_order_does_not_change_identity(self):
        self.assertEqual(self.select(),self.select(tuple(reversed(self.rows))))

    def test_forward_monitors_do_not_change_frozen_choice(self):
        selected=self.select();before=copy.deepcopy(selected)
        first=monitor_frozen_selection(selected,({'candidate':'a','season':2026,'log_loss':.9},
                                                {'candidate':'MARKET','season':2026,'log_loss':.1}))
        self.assertEqual(first['selected'],'a');self.assertEqual(selected,before)
        self.assertEqual(first['observations'][0]['candidate'],'MARKET')

    def test_tampered_selection_rejected(self):
        selected=self.select();selected['selected']='MARKET'
        with self.assertRaisesRegex(ValueError,'changed'):monitor_frozen_selection(selected,())

    def test_bad_monitoring_identity_rejected(self):
        selected=self.select()
        for rows in (({'candidate':'a','season':2025,'log_loss':.1},),
                     ({'candidate':'undeclared','season':2026,'log_loss':.1},),
                     ({'candidate':'a','season':2026,'log_loss':.1},)*2):
            with self.subTest(rows=rows),self.assertRaises(ValueError):monitor_frozen_selection(selected,rows)

    def test_contract_cannot_admit_forward_selection_year(self):
        for change in ({'historical_seasons':(2024,2026)},{'forward_first_season':True},
                       {'candidates':('MARKET','a','a')},{'protocol':'unspecified'}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.select(contract=replace(self.contract,**change))

    def test_naive_or_boolean_identity_rejected(self):
        with self.assertRaises(ValueError):self.select(contract=replace(self.contract,frozen_at=self.clock.replace(tzinfo=None)))
        with self.assertRaises(ValueError):self.select(self.rows[:-1]+(replace(self.rows[-1],games=True),))


if __name__=='__main__':unittest.main()
