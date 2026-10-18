"""Offline synthetic checks; no credentials, network, or estimator fitting."""
import copy
import json
import unittest
from source_adjudication import adjudicate_cfbd_drives, fixture_inputs

SHA = 'a' * 64
AT = '2026-10-18T02:02:44+00:00'


class SourceAdjudicationTests(unittest.TestCase):
    def run_case(self, rows=None, **kw):
        return adjudicate_cfbd_drives(fixture_inputs() if rows is None else rows,
                                     source_sha256=kw.get('source_sha256', SHA),
                                     source_observed_at=kw.get('source_observed_at', AT))

    def changed(self, **kw):
        rows = fixture_inputs(); rows[1].update(kw); return rows

    def middle(self, rows=None):
        return next(x for x in self.run_case(rows)['period_candidates'] if x['drive_id'] == '10012')

    def test_corroborated_exact_candidate(self):
        r = self.middle(); self.assertEqual(r['candidate_end_period'], 2)
        self.assertEqual(r['status'], 'derived_candidate_corroborated')

    def test_source_unchanged(self):
        rows = fixture_inputs(); before = copy.deepcopy(rows); self.run_case(rows); self.assertEqual(rows, before)

    def test_no_automatic_model_insertion(self):
        a = self.run_case()['audit']; self.assertFalse(a['automatic_serving_authorized'])
        self.assertEqual((a['model_feature_insertions'], a['new_model_fits'], a['source_corrections']), (0, 0, 0))

    def test_preserve_raw_period(self):
        r = self.middle(); self.assertEqual(r['original_end_period'], 0); self.assertTrue(r['derived_not_authoritative'])

    def test_source_provenance(self):
        r = self.middle(); self.assertEqual(r['source_sha256'], SHA); self.assertEqual(r['source_observed_at'], AT)
        self.assertIsNone(r['source_publication_at']); self.assertEqual(len(r['row_sha256']), 64)

    def test_known_valid_period_untouched(self):
        rows = self.changed(endPeriod=2); self.assertEqual(self.run_case(rows)['period_candidates'], [])

    def test_overtime_not_inferred(self):
        rows = self.changed(startPeriod=5, endPeriod=0)
        self.assertNotEqual(self.middle(rows)['status'], 'derived_candidate_corroborated')
        self.assertIsNone(self.middle(rows)['candidate_end_period'])

    def test_invalid_start_period(self):
        r = self.middle(self.changed(startPeriod=0)); self.assertEqual(r['reason'], 'invalid_or_overtime_start_period')

    def test_boolean_period_rejected(self):
        r = self.middle(self.changed(startPeriod=True)); self.assertEqual(r['reason'], 'invalid_or_overtime_start_period')

    def test_string_period_rejected(self):
        r = self.middle(self.changed(startPeriod='2')); self.assertEqual(r['reason'], 'invalid_or_overtime_start_period')

    def test_float_start_period_rejected(self):
        r = self.middle(self.changed(startPeriod=2.0)); self.assertEqual(r['reason'], 'invalid_or_overtime_start_period')

    def test_boolean_end_period_no_inference(self):
        r = self.middle(self.changed(endPeriod=False)); self.assertEqual(r['reason'], 'invalid_end_period_representation')
        self.assertIsNone(r['candidate_end_period'])

    def test_string_end_period_no_inference(self):
        r = self.middle(self.changed(endPeriod='0')); self.assertEqual(r['reason'], 'invalid_end_period_representation')

    def test_previous_backward_period_not_corroboration(self):
        rows = fixture_inputs(); rows[0]['startPeriod'] = 3; rows[0]['endPeriod'] = 2
        self.assertEqual(self.middle(rows)['status'], 'derived_candidate_uncorroborated')

    def test_clock_boolean_rejected(self):
        r = self.middle(self.changed(startTime={'minutes': True, 'seconds': 20})); self.assertEqual(r['reason'], 'invalid_clock_or_elapsed')

    def test_clock_string_rejected(self):
        r = self.middle(self.changed(endTime={'minutes': '6', 'seconds': 40})); self.assertEqual(r['reason'], 'invalid_clock_or_elapsed')

    def test_clock_minutes_out_of_range(self):
        r = self.middle(self.changed(startTime={'minutes': 16, 'seconds': 0})); self.assertEqual(r['reason'], 'invalid_clock_or_elapsed')

    def test_clock_seconds_out_of_range(self):
        r = self.middle(self.changed(startTime={'minutes': 8, 'seconds': 60})); self.assertEqual(r['reason'], 'invalid_clock_or_elapsed')

    def test_clock_15_minutes_plus_seconds_invalid(self):
        r = self.middle(self.changed(startTime={'minutes': 15, 'seconds': 1})); self.assertEqual(r['reason'], 'invalid_clock_or_elapsed')

    def test_missing_clock(self):
        r = self.middle(self.changed(endTime=None)); self.assertEqual(r['reason'], 'invalid_clock_or_elapsed')

    def test_long_duration_fails_closed(self):
        r = self.middle(self.changed(elapsed={'minutes': 16, 'seconds': 0})); self.assertEqual(r['reason'], 'invalid_clock_or_elapsed')

    def test_no_integer_solution(self):
        r = self.middle(self.changed(elapsed={'minutes': 1, 'seconds': 41})); self.assertEqual(r['reason'], 'clock_equation_has_no_integer_period')

    def test_boundary_clock_not_inferred(self):
        rows = self.changed(endTime={'minutes': 0, 'seconds': 0}, elapsed={'minutes': 8, 'seconds': 20})
        self.assertEqual(self.middle(rows)['status'], 'boundary_ambiguous')

    def test_quarter_start_boundary_ambiguous(self):
        rows = self.changed(startTime={'minutes': 15, 'seconds': 0}, elapsed={'minutes': 8, 'seconds': 20})
        self.assertEqual(self.middle(rows)['status'], 'boundary_ambiguous')

    def test_next_neighbor_conflict(self):
        rows = fixture_inputs(); rows[2]['startTime'] = {'minutes': 7, 'seconds': 0}
        self.assertEqual(self.middle(rows)['status'], 'neighbor_conflict')

    def test_previous_neighbor_conflict(self):
        rows = fixture_inputs(); rows[0]['endTime'] = {'minutes': 7, 'seconds': 0}
        self.assertEqual(self.middle(rows)['status'], 'neighbor_conflict')

    def test_missing_neighbor_explicit(self):
        self.assertEqual(self.middle(fixture_inputs()[:2])['status'], 'derived_candidate_uncorroborated')

    def test_neighbor_gap_not_bridged(self):
        rows = fixture_inputs(); rows[2]['driveNumber'] = 4
        self.assertEqual(self.middle(rows)['status'], 'derived_candidate_uncorroborated')

    def test_neighbor_invalid_clock_explicit(self):
        rows = fixture_inputs(); rows[2]['startTime'] = None
        self.assertEqual(self.middle(rows)['status'], 'derived_candidate_uncorroborated')

    def test_neighbor_duplicate_explicit(self):
        rows = fixture_inputs(); extra = copy.deepcopy(rows[2]); extra['id'] = '999'; rows.append(extra)
        self.assertEqual(self.middle(rows)['status'], 'derived_candidate_uncorroborated')

    def test_current_duplicate_drive_id(self):
        rows = fixture_inputs(); rows.append(copy.deepcopy(rows[1]))
        self.assertEqual(self.middle(rows)['reason'], 'duplicate_drive_identity_or_number')

    def test_current_duplicate_drive_number(self):
        rows = fixture_inputs(); extra = copy.deepcopy(rows[1]); extra['id'] = '999'; rows.append(extra)
        self.assertEqual(self.middle(rows)['reason'], 'duplicate_drive_identity_or_number')

    def test_unknown_result_never_mapped(self):
        rows = self.changed(driveResult='Uncategorized'); r = self.run_case(rows)['unsupported_results'][0]
        self.assertEqual(r['original_result'], 'Uncategorized'); self.assertIsNone(r['mapped_result'])

    def test_return_td_not_equated_to_offensive_td(self):
        rows = self.changed(driveResult='KICKOFF RETURN TD'); self.assertEqual(self.run_case(rows)['audit']['unsupported_result_rows'], 1)

    def test_blocked_fg_not_equated_to_missed_fg(self):
        rows = self.changed(driveResult='BLOCKED FG'); self.assertIsNone(self.run_case(rows)['unsupported_results'][0]['mapped_result'])

    def test_known_result_not_flagged(self):
        self.assertEqual(self.run_case()['unsupported_results'], [])

    def test_invalid_identity_explicit(self):
        rows = self.changed(gameId=True); self.assertEqual(self.run_case(rows)['audit']['invalid_identity_rows'], 1)

    def test_missing_drive_number_explicit(self):
        rows = self.changed(driveNumber=None); self.assertEqual(self.run_case(rows)['audit']['invalid_identity_rows'], 1)

    def test_empty_input(self):
        self.assertEqual(self.run_case([])['audit']['input_rows'], 0)

    def test_maximum_bound(self):
        with self.assertRaises(ValueError): self.run_case([None] * 50001)

    def test_list_required(self):
        with self.assertRaises(ValueError): self.run_case({})

    def test_bad_hash_rejected(self):
        with self.assertRaises(ValueError): self.run_case(source_sha256='not-a-hash')

    def test_naive_observation_rejected(self):
        with self.assertRaises(ValueError): self.run_case(source_observed_at='2026-10-18T02:02:44')

    def test_serializable(self):
        json.dumps(self.run_case(), allow_nan=False)

    def test_negative_candidate_rejected(self):
        rows = self.changed(startPeriod=1, startTime={'minutes': 15, 'seconds': 0}, endTime={'minutes': 0, 'seconds': 0}, elapsed={'minutes': 0, 'seconds': 0})
        self.assertEqual(self.middle(rows)['reason'], 'candidate_not_regulation_or_precedes_start')

    def test_cross_quarter_solution(self):
        rows = self.changed(startPeriod=1, startTime={'minutes': 1, 'seconds': 0}, endTime={'minutes': 14, 'seconds': 0}, elapsed={'minutes': 2, 'seconds': 0})
        rows[0]['startPeriod'] = 1; rows[0]['endPeriod'] = 1; rows[0]['endTime'] = {'minutes': 1, 'seconds': 0}
        rows[2]['startPeriod'] = 2; rows[2]['endPeriod'] = 2; rows[2]['startTime'] = {'minutes': 14, 'seconds': 0}
        self.assertEqual(self.middle(rows)['candidate_end_period'], 2)
        self.assertEqual(self.middle(rows)['status'], 'derived_candidate_corroborated')

    def test_halftime_crossing_rejected(self):
        rows = self.changed(startPeriod=2, startTime={'minutes': 1, 'seconds': 0}, endTime={'minutes': 14, 'seconds': 0}, elapsed={'minutes': 2, 'seconds': 0})
        self.assertEqual(self.middle(rows)['reason'], 'drive_cannot_cross_halftime')
        self.assertIsNone(self.middle(rows)['candidate_end_period'])

    def test_extended_fixture_edges(self):
        result = self.run_case(fixture_inputs(include_edge_cases=True))
        self.assertEqual(result['audit']['unsupported_result_rows'], 1)
        self.assertEqual(result['audit']['period_status_counts']['boundary_ambiguous'], 1)

    def test_overtime_candidate_rejected(self):
        rows = self.changed(startPeriod=4, startTime={'minutes': 1, 'seconds': 0}, endTime={'minutes': 14, 'seconds': 0}, elapsed={'minutes': 2, 'seconds': 0})
        self.assertEqual(self.middle(rows)['reason'], 'candidate_not_regulation_or_precedes_start')


if __name__ == '__main__':
    unittest.main(verbosity=2)
