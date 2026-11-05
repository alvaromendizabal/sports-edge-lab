import unittest
from injury_time import Availability,views,paired_changes

class InjuryTimeTests(unittest.TestCase):
    def test_late_recovered_report_can_display_without_earlier_capture(self):
        row=Availability('2035-01-01T17:00:00Z','2035-01-02T01:00:00Z','Out')
        result=views(row,boundary='2035-01-01T18:00:00Z',tip='2035-01-01T20:00:00Z')
        self.assertTrue(result['source_supported']);self.assertFalse(result['captured']);self.assertEqual(result['display'],'Out')
    def test_latest_pregame_does_not_rewrite_two_hour_issue(self):
        row=Availability('2035-01-01T19:30:00Z','2035-01-01T19:31:00Z','Out')
        self.assertFalse(views(row,boundary='2035-01-01T18:00:00Z',tip='2035-01-01T20:00:00Z')['captured'])
        self.assertTrue(views(row,boundary='2035-01-01T19:59:00Z',tip='2035-01-01T20:00:00Z')['captured'])
    def test_missing_is_not_healthy(self):
        self.assertFalse(views(None,boundary='2035-01-01T18:00:00Z',tip='2035-01-01T20:00:00Z')['healthy_claim'])
    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):views(None,boundary='2035-01-01T18:00:00',tip='2035-01-01T20:00:00Z')
    def test_boundary_at_tip_rejected(self):
        with self.assertRaises(ValueError):views(None,boundary='2035-01-01T20:00:00Z',tip='2035-01-01T20:00:00Z')
    def test_same_population_for_loss_change(self):
        r=paired_changes({'a':.3,'b':.8},{'a':.2,'c':0})
        self.assertEqual(r['shared_games'],['a']);self.assertAlmostEqual(r['mean_loss_change'],-.1)
        self.assertEqual(r['unmatched_base'],['b']);self.assertEqual(r['unmatched_challenger'],['c'])
