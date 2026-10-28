"""Stopped owner evidence must not become accepted science through reporting."""
import unittest
from examples.basketball_contracts.evidence_b004 import load_evidence,validate,render,REPORT

class StoppedEvidenceTests(unittest.TestCase):
    def setUp(self):self.value=load_evidence()
    def test_saved_document_is_reproducible(self):self.assertEqual(render(self.value),REPORT.read_text())
    def test_resource_stop_cannot_be_relabelled_accepted(self):
        self.value['owner_execution']['accepted_release']=True
        with self.assertRaisesRegex(ValueError,'stopped execution'):validate(self.value)
    def test_imports_cannot_inflate_new_fits(self):
        self.value['owner_execution']['new_real_units']+=216
        with self.assertRaisesRegex(ValueError,'imported aliases'):validate(self.value)
    def test_budget_cannot_reset(self):
        self.value['accounting']['remaining_work_seconds']=4500
        with self.assertRaisesRegex(ValueError,'budget'):validate(self.value)
    def test_one_year_gain_cannot_earn_promotion(self):
        self.value['challengers'][1]['promoted']=True
        with self.assertRaisesRegex(ValueError,'promotion'):validate(self.value)
    def test_current_outcomes_cannot_enter_gate(self):
        self.value['challengers'][0]['per_season'][1]['season']=2027
        with self.assertRaisesRegex(ValueError,'protected'):validate(self.value)
    def test_point_component_cannot_be_hidden_by_joint_gain(self):
        g=next(g for g in self.value['challengers'] if g['league']=='ncaam' and g['target']=='points')
        g['per_season'][0]['conditions']['margin_rmse_no_regression']=True
        with self.assertRaisesRegex(ValueError,'per-season'):validate(self.value)
