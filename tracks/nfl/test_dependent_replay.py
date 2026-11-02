"""Behavioral tests of exact identity, formula checks and retained byte replay."""
import copy
import hashlib
import json
import math
import unittest

from dependent_replay import demo, recover_original_inputs


class DependentReplayTests(unittest.TestCase):
    def setUp(self):
        self.row = {'identity': {'event': 'invented', 'source': 'source', 'model': 'model', 'cutoff': 'clock'},
                    'baseline': .5, 'independent': {'scale': 2., 'offset': .25},
                    'derived': {'shifted': .75, 'scaled': 1.}}
        self.body = (json.dumps(self.row, indent=2) + '\n').encode()

    def recover(self, replay=None, body=None, tolerance=1e-12):
        body = self.body if body is None else body
        return recover_original_inputs(body, expected_sha256=hashlib.sha256(body).hexdigest(),
                                       recomputed=self.row if replay is None else replay,
                                       baseline_abs_tolerance=tolerance)

    def varied(self, base):
        row = copy.deepcopy(self.row); row['baseline'] = base
        row['derived'] = {'shifted': base+.25, 'scaled': base*2.}
        return row

    def test_equal_replay_retains_original_whitespace_and_newline(self):
        body, receipt = self.recover()
        self.assertIs(body, self.body)
        self.assertFalse(receipt['original_bytes_changed'])
        self.assertEqual(receipt['training_hash_tolerance'], 0)

    def test_single_ulp_changes_dependent_fields_but_accepts_declared_baseline(self):
        replay = self.varied(math.nextafter(.5, 1.))
        self.assertNotEqual(self.row['derived'], replay['derived'])
        before = copy.deepcopy(replay)
        body, receipt = self.recover(replay)
        self.assertEqual(body, self.body); self.assertEqual(replay, before)
        self.assertGreater(receipt['baseline_abs_difference'], 0)

    def test_no_blanket_tolerance_on_independent_fields(self):
        replay = copy.deepcopy(self.row)
        replay['independent']['offset'] = math.nextafter(.25, 1.)
        replay['derived']['shifted'] = .5 + replay['independent']['offset']
        with self.assertRaisesRegex(ValueError, 'Exact field identity'):
            self.recover(replay)

    def test_no_tolerance_on_derived_formula(self):
        replay = copy.deepcopy(self.row); replay['derived']['scaled'] = math.nextafter(1., 2.)
        with self.assertRaisesRegex(ValueError, 'formula'):
            self.recover(replay)

    def test_original_must_obey_formula_too(self):
        altered = copy.deepcopy(self.row); altered['derived']['scaled'] += .01
        with self.assertRaisesRegex(ValueError, 'formula'):
            self.recover(body=json.dumps(altered).encode())

    def test_zero_tolerance_accepts_equal_only(self):
        self.recover(tolerance=0)
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.recover(self.varied(math.nextafter(.5, 1.)), tolerance=0)

    def test_exclusive_tolerance_boundary(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.recover(self.varied(.625), tolerance=.125)
        self.recover(self.varied(.625), tolerance=.126)

    def test_changed_identity_is_not_numerically_waived(self):
        for key in self.row['identity']:
            replay = copy.deepcopy(self.row); replay['identity'][key] += '-changed'
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'identity'):
                self.recover(replay)

    def test_independent_numeric_type_changes_are_not_waived(self):
        replay = copy.deepcopy(self.row); replay['independent']['scale'] = 2
        with self.assertRaisesRegex(ValueError, 'Exact field identity'):
            self.recover(replay)

    def test_wrong_hash_refuses_before_json_parsing(self):
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            recover_original_inputs(b'not-json', expected_sha256='0'*64,
                                    recomputed=self.row, baseline_abs_tolerance=1e-12)

    def test_invalid_hash_format(self):
        for pin in ('', 'A'*64, None, 'g'*64):
            with self.subTest(pin=pin), self.assertRaises(ValueError):
                recover_original_inputs(self.body, expected_sha256=pin,
                                        recomputed=self.row, baseline_abs_tolerance=1e-12)

    def test_duplicate_json_keys_are_rejected(self):
        body = self.body.replace(b'"baseline": 0.5,', b'"baseline": 0.5,"baseline": 0.5,')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.recover(body=body)

    def test_nonfinite_and_boolean_numbers_are_rejected(self):
        for value in (True, float('inf'), float('-inf'), float('nan')):
            replay = copy.deepcopy(self.row); replay['baseline'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.recover(replay)

    def test_nan_json_constants_are_rejected(self):
        body = self.body.replace(b'"baseline": 0.5', b'"baseline": NaN')
        with self.assertRaisesRegex(ValueError, 'Non-finite'):
            self.recover(body=body)

    def test_missing_extra_and_unknown_fields_fail_closed(self):
        for field in ('identity', 'independent', 'derived'):
            for action in ('missing', 'extra'):
                replay = copy.deepcopy(self.row)
                if action == 'missing': replay[field].pop(next(iter(replay[field])))
                else: replay[field]['unregistered'] = 1
                with self.subTest(field=field, action=action), self.assertRaises(ValueError):
                    self.recover(replay)

    def test_invalid_tolerances(self):
        for tolerance in (-1, True, '1e-9', float('nan'), float('inf')):
            with self.subTest(tolerance=tolerance), self.assertRaises(ValueError):
                self.recover(tolerance=tolerance)

    def test_overflow_in_formula_is_rejected(self):
        replay = copy.deepcopy(self.row); replay['baseline'] = 1e308
        with self.assertRaises(ValueError): self.recover(replay)

    def test_demo_is_explicit_about_credit(self):
        result = demo()
        self.assertEqual(result['evidence_class'], 'INVENTED_ENGINEERING_FIXTURE')
        self.assertFalse(result['ordinary_exact_derived_comparison'])
        self.assertEqual(result['receipt']['new_fits'], 0)
        self.assertEqual(result['receipt']['new_forecast_issues'], 0)
        self.assertFalse(result['receipt']['owner_acceptance_claimed'])


if __name__ == '__main__':
    unittest.main()
