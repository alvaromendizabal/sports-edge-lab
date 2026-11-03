"""Meaningful negative cases; every event, probability and price is invented."""
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import contracts as c

def prediction(event='invented-1', p=0.7, actual=1, league='ncaam'):
    return {'league': league, 'event_id': event, 'home_id': 'invented-home', 'away_id': 'invented-away', 'event_time': '2026-03-01T18:00:00+00:00', 'cutoff_time': '2026-03-01T16:00:00+00:00', 'target': 'win', 'settlement': c.SETTLEMENT, 'prediction': p, 'actual': actual, 'feature_available_at': '2026-03-01T14:00:00+00:00', 'training_label_max': '2026-02-28T12:00:00+00:00', 'model_version': 'invented-v1', 'track': 'rolling_reconstructed', 'issued_at': None, 'reconstruction_at': '2026-03-03T12:00:00+00:00', 'label_available_at': '2026-03-02T18:00:00+00:00'}

def quote(row, provider='Kalshi', p=0.6):
    q = {k: row[k] for k in ('league', 'event_id', 'home_id', 'away_id', 'event_time', 'cutoff_time', 'target', 'settlement')}
    return {**q, 'provider': provider, 'prediction': p, 'available_at': '2026-03-01T15:50:00+00:00', 'historical_availability_verified': True}

class MetricTests(unittest.TestCase):

    def test_exact_probability_metrics_and_half_credit_ties(self):
        r = c.win_metrics([1, 0, 1], [0.8, 0.2, 0.5])
        self.assertAlmostEqual(r['LogLoss'], (-2 * math.log(0.8) - math.log(0.5)) / 3)
        self.assertAlmostEqual(r['Brier'], (0.04 + 0.04 + 0.25) / 3)
        self.assertAlmostEqual(r['Accuracy'], 2.5 / 3)
        self.assertEqual(r['probability_ties'], 1)
        self.assertEqual(sum((b['N'] for b in r['calibration_bins'])), 3)

    def test_auc_uses_tied_mid_ranks_and_is_none_for_one_class(self):
        self.assertEqual(c.win_metrics([0, 1], [0.5, 0.5])['ROC_AUC'], 0.5)
        self.assertEqual(c.win_metrics([0, 1, 0, 1], [0.1, 0.8, 0.2, 0.9])['ROC_AUC'], 1.0)
        self.assertIsNone(c.win_metrics([1, 1], [0.2, 0.8])['ROC_AUC'])

    def test_brier_does_not_clip_endpoint_probabilities(self):
        r = c.win_metrics([1, 0], [0.0, 1.0])
        self.assertEqual(r['Brier'], 1.0)
        self.assertTrue(math.isfinite(r['LogLoss']))
        self.assertEqual(r['Accuracy'], 0.0)

    def test_nonfinite_boolean_and_wrong_probability_rejected(self):
        for bad in (float('nan'), float('inf'), True, -0.1, 1.1):
            with self.assertRaises(ValueError):
                c.win_metrics([1], [bad])

    def test_margin_units_bias_and_sign_accuracy(self):
        r = c.point_metrics([4, -2, 6], [2, 0, 9], 'margin')
        self.assertAlmostEqual(r['MAE'], 7 / 3)
        self.assertAlmostEqual(r['RMSE'], math.sqrt(17 / 3))
        self.assertEqual(r['Bias'], 1)
        self.assertAlmostEqual(r['DirectionAccuracy'], 2.5 / 3)

    def test_total_point_errors_do_not_invent_over_under_accuracy(self):
        self.assertIsNone(c.point_metrics([140, 150], [145, 146], 'total')['OverUnderAccuracy'])
        r = c.point_metrics([140, 150, 160], [145, 147, 158], 'total', lines=[140, 148, 158])
        self.assertEqual(r['actual_pushes'], 1)
        self.assertEqual(r['prediction_abstentions'], 1)
        self.assertEqual(r['OverUnderN'], 1)
        self.assertEqual(r['OverUnderAccuracy'], 0)

class ClockAndPairTests(unittest.TestCase):

    def test_equivalent_UTC_spellings_match(self):
        p = prediction()
        q = quote(p)
        q['event_time'] = '2026-03-01T18:00:00Z'
        self.assertEqual(c.identity(p), c.identity(q))

    def test_equal_cutoff_information_is_excluded(self):
        for name in ('feature_available_at', 'training_label_max'):
            p = prediction()
            p[name] = p['cutoff_time']
            with self.assertRaisesRegex(ValueError, 'must precede cutoff'):
                c.validate_prediction(p)

    def test_naive_time_and_after_horizon_forecast_are_rejected(self):
        p = prediction()
        p['event_time'] = '2026-03-01T18:00:00'
        with self.assertRaisesRegex(ValueError, 'naive'):
            c.validate_prediction(p)
        p = prediction()
        p['cutoff_time'] = '2026-03-01T17:30:00+00:00'
        with self.assertRaisesRegex(ValueError, 'horizon'):
            c.validate_prediction(p)

    def test_reconstruction_cannot_claim_issue(self):
        p = prediction()
        p['issued_at'] = p['cutoff_time']
        with self.assertRaisesRegex(ValueError, 'manufacture an issue'):
            c.validate_prediction(p)

    def test_model_creation_cannot_precede_its_training_labels(self):
        p = prediction()
        p.update(track='issued_prospective', issued_at=p['cutoff_time'],
                 model_created_at='2026-02-28T12:00:00+00:00')
        with self.assertRaisesRegex(ValueError, 'training label release'):
            c.validate_prediction(p)
        p['model_created_at'] = '2026-02-28T12:00:01+00:00'
        self.assertEqual(c.validate_prediction(p), c.identity(p))

    def test_tracks_cannot_be_pooled(self):
        a = prediction()
        b = prediction('invented-2')
        b['track'] = 'frozen_original'
        with self.assertRaisesRegex(ValueError, 'remain separate'):
            c.score_paired([a, b], [], evaluated_at='2026-03-04T00:00:00Z')

    def test_each_provider_gets_its_exact_shared_cohort(self):
        a = prediction('invented-a', 0.8, 1)
        b = prediction('invented-b', 0.2, 0)
        q = [quote(a), quote(b), quote(a, 'DraftKings')]
        r = c.score_paired([a, b], q, evaluated_at='2026-03-04T00:00:00Z')
        self.assertEqual(r['unmatched_by_provider'], {'Kalshi': 0, 'Polymarket': 2, 'DraftKings': 1})
        for panel in r['panels']:
            self.assertEqual(panel['model']['N'], panel['reference']['N'])
        self.assertEqual({p['provider']: p['model']['N'] for p in r['panels']}, {'Kalshi': 2, 'DraftKings': 1})

    def test_same_count_different_games_are_not_paired(self):
        a = prediction('invented-a')
        b = prediction('invented-b')
        q = quote(b)
        r = c.score_paired([a], [q], evaluated_at='2026-03-04T00:00:00Z')
        self.assertEqual(r['panels'], [])

    def test_changed_ordered_teams_or_settlement_never_matches(self):
        a = prediction()
        q = quote(a)
        q['home_id'], q['away_id'] = (q['away_id'], q['home_id'])
        self.assertEqual(c.score_paired([a], [q], evaluated_at='2026-03-04T00:00:00Z')['panels'], [])
        q = quote(a)
        q['settlement'] = 'regulation_only'
        r = c.score_paired([a], [q], evaluated_at='2026-03-04T00:00:00Z')
        self.assertEqual(r['panels'], [])
        self.assertEqual(len(r['rejected_quotes']), 1)

    def test_mens_and_womens_metrics_are_separate(self):
        a = prediction(p=0.9, actual=1)
        b = prediction(p=0.1, actual=1, league='ncaaw')
        r = c.score_paired([a, b], [quote(a), quote(b)], evaluated_at='2026-03-04T00:00:00Z')
        self.assertEqual({p['league']: p['model']['N'] for p in r['panels']}, {'ncaam': 1, 'ncaaw': 1})

    def test_late_and_unproven_quote_is_a_recorded_gap(self):
        p = prediction()
        q = quote(p)
        q['available_at'] = '2026-03-01T16:01:00Z'
        r = c.score_paired([p], [q], evaluated_at='2026-03-04T00:00:00Z')
        self.assertEqual(r['panels'], [])
        self.assertEqual(len(r['rejected_quotes']), 1)
        q = quote(p)
        q['historical_availability_verified'] = False
        self.assertEqual(c.score_paired([p], [q], evaluated_at='2026-03-04T00:00:00Z')['panels'], [])

    def test_prospective_pair_cannot_use_quote_received_after_issue(self):
        p = prediction()
        p.update(track='issued_prospective', issued_at='2026-03-01T16:00:00Z', cutoff_time='2026-03-01T17:00:00Z', model_created_at='2026-03-01T15:00:00Z')
        q = quote(p)
        q['available_at'] = '2026-03-01T16:10:00Z'
        r = c.score_paired([p], [q], evaluated_at='2026-03-04T00:00:00Z')
        self.assertEqual(r['panels'], [])
        self.assertIn('after model issue', r['rejected_quotes'][0]['reason'])

    def test_future_actual_is_not_scored(self):
        p = prediction()
        r = c.score_paired([p], [quote(p)], evaluated_at='2026-03-02T00:00:00Z')
        self.assertEqual(r['panels'], [])

    def test_duplicate_source_and_extra_provider_are_errors(self):
        p = prediction()
        q = quote(p)
        with self.assertRaisesRegex(ValueError, 'duplicate provider'):
            c.score_paired([p], [q, q], evaluated_at='2026-03-04T00:00:00Z')
        q['provider'] = 'UNDECLARED'
        with self.assertRaisesRegex(ValueError, 'scope'):
            c.score_paired([p], [q], evaluated_at='2026-03-04T00:00:00Z')

    def test_winning_and_losing_disagreements_are_both_preserved(self):
        a = prediction('invented-a', 0.8, 1)
        b = prediction('invented-b', 0.8, 0)
        r = c.score_paired([a, b], [quote(a, p=0.3), quote(b, p=0.3)], evaluated_at='2026-03-04T00:00:00Z')
        self.assertEqual([x['model_correct'] for x in r['panels'][0]['disagreements']], [True, False])

class FittingAndPayoffTests(unittest.TestCase):

    def history(self):
        p = prediction()
        p.update(win=1, margin=6, total=146)
        q = copy.deepcopy(p)
        q['label_available_at'] = '2026-03-10T00:00:00Z'
        q.update(win=0, margin=-40, total=180)
        return [p, q]

    def test_future_label_poison_does_not_change_earlier_fit(self):
        rows = self.history()
        a = c.toy_fit(rows, '2026-03-04T00:00:00Z', 'ncaam')
        rows[1].update(win=1, margin=42, total=200)
        self.assertEqual(a, c.toy_fit(rows, '2026-03-04T00:00:00Z', 'ncaam'))
        self.assertNotEqual(a, c.toy_fit(rows, '2026-03-11T00:00:00Z', 'ncaam'))

    def test_exact_training_release_boundary_excluded(self):
        rows = self.history()
        self.assertEqual(c.toy_fit(rows, '2026-03-10T00:00:00Z', 'ncaam')['training_rows'], 1)

    def test_unknown_fees_cannot_be_treated_as_zero(self):
        q = quote(prediction())
        q.update(executable=True, fee_verified=False)
        self.assertEqual(c.hypothetical_win_decision(0.7, q)['selection'], 'NO BET')

    def test_binary_contract_uses_ask_and_fee_with_no_outcome_in_selection(self):
        q = quote(prediction())
        q.update(executable=True, fee_verified=True, price_type='binary_contract', home_ask=0.6, away_ask=0.43, home_fee_per_unit=0.01, away_fee_per_unit=0.01)
        before = c.hypothetical_win_decision(0.7, q)
        win = c.hypothetical_win_decision(0.7, q, 1)
        loss = c.hypothetical_win_decision(0.7, q, 0)
        self.assertEqual(before['selection'], win['selection'])
        self.assertEqual(win['selection'], loss['selection'])
        self.assertAlmostEqual(before['expected_value_per_unit'], 0.09)
        self.assertAlmostEqual(win['hypothetical_profit'], 0.39)
        self.assertAlmostEqual(loss['hypothetical_profit'], -0.61)
        self.assertEqual(loss['orders'], 0)

    def test_no_edge_is_no_bet_and_demo_is_deterministic(self):
        q = quote(prediction())
        q.update(executable=True, fee_verified=True, price_type='decimal', home_decimal=1.9, away_decimal=1.9, home_fee_per_unit=0.0, away_fee_per_unit=0.0)
        self.assertEqual(c.hypothetical_win_decision(0.5, q)['selection'], 'NO BET')
        a = c.demo()
        self.assertEqual(a, c.demo())
        self.assertTrue(a['fixture_only'])
        self.assertEqual(a['orders'], 0)

class StreamBoundaryTests(unittest.TestCase):

    class Wrapper:

        def __init__(self, body):
            self.raw = io.BytesIO(body)
            self.entered = False
            self.closed = False

        def __enter__(self):
            self.entered = True
            return object()

        def __exit__(self, *args):
            self.close()

        def read(self, n):
            return self.raw.read(n)

        def close(self):
            self.closed = True
            self.raw.close()

    def test_different_context_return_does_not_change_reader_identity(self):
        data = b'invented artifact'
        stream = self.Wrapper(data)
        self.assertEqual(c.verified_read(stream, {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}, chunk_size=2), data)
        self.assertTrue(stream.closed)
        self.assertFalse(stream.entered)

    def test_corruption_and_oversize_always_close(self):
        for body, pin, maximum in [(b'changed', {'bytes': 7, 'sha256': '0' * 64}, 100), (b'oversize', {'bytes': 2, 'sha256': '0' * 64}, 2)]:
            stream = self.Wrapper(body)
            with self.assertRaises(ValueError):
                c.verified_read(stream, pin, maximum=maximum)
            self.assertTrue(stream.closed)
if __name__ == '__main__':
    unittest.main()
