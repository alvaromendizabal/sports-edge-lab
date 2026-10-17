"""Synthetic classic-chart period arithmetic only; no publisher content."""
import unittest
from gap_classic import regulation_end_period, ParseRejected

class ClassicMathTests(unittest.TestCase):
    def test_same_quarter(self):
        self.assertEqual(regulation_end_period(1,'10:00','07:00','03:00'),1)
    def test_cross_quarter(self):
        self.assertEqual(regulation_end_period(1,'01:00','14:00','02:00'),2)
    def test_second_half_cross_quarter(self):
        self.assertEqual(regulation_end_period(3,'01:00','14:00','02:00'),4)
    def test_cross_halftime_rejected(self):
        with self.assertRaises(ParseRejected):regulation_end_period(2,'01:00','14:00','02:00')
    def test_inconsistent_top_rejected(self):
        with self.assertRaises(ParseRejected):regulation_end_period(1,'10:00','07:00','04:00')
    def test_bad_clock_rejected(self):
        with self.assertRaises(ParseRejected):regulation_end_period(1,'10:99','07:00','03:00')
    def test_out_of_range_clock_rejected(self):
        with self.assertRaises(ParseRejected):regulation_end_period(1,'16:00','07:00','09:00')
    def test_negative_duration_rejected(self):
        with self.assertRaises(ParseRejected):regulation_end_period(1,'10:00','07:00','-03:00')

if __name__=='__main__': unittest.main()
