import json
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from examples.fbs_contracts.core import FitJournal, atomic_json, digest, fit_model, fixture, pregame_rows, run_demo, source_catalog


class InformationTimeTests(unittest.TestCase):
    def test_fbs_visitors_remain_in_population(self):
        rows = pregame_rows(fixture())
        self.assertEqual(len(rows), 128)
        self.assertEqual(sum(row['population'] == 'FBS_FCS' for row in rows), 32)

    def test_fcs_only_game_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'FCS-only'):
            pregame_rows([replace(fixture()[0], home_fbs=False, away_fbs=False)])

    def test_unproved_duplicate_native_id_is_rejected(self):
        game = fixture()[0]
        with self.assertRaisesRegex(ValueError, 'duplicate native'):
            pregame_rows([game, replace(game, home='invented_changed_home')])

    def test_unknown_population_is_not_coerced_to_true(self):
        with self.assertRaisesRegex(ValueError, 'explicit'):
            pregame_rows([replace(fixture()[0], home_fbs='False')])

    def test_late_market_observation_is_not_backdated(self):
        game = fixture()[0]
        with self.assertRaisesRegex(ValueError, 'market unavailable'):
            pregame_rows([replace(game, market_observed_at=game.kickoff)])

    def test_naive_clock_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'timezone-aware'):
            pregame_rows([replace(fixture()[0], kickoff='2023-09-01T20:00:00')])

    def test_same_game_outcome_cannot_change_own_feature(self):
        games = fixture()
        before = pregame_rows(games)
        changed = [replace(games[0], home_points=100, away_points=0), *games[1:]]
        after = pregame_rows(changed)
        self.assertEqual(before[0]['football_strength'], after[0]['football_strength'])
        self.assertNotIn(games[0].game_id, after[0]['source_game_ids'])

    def test_late_observed_prior_outcome_is_excluded(self):
        games = fixture()
        delayed = replace(games[0], outcome_observed_at='2027-01-01T00:00:00Z')
        rows = pregame_rows([delayed, *games[1:]])
        self.assertTrue(all(delayed.game_id not in row['source_game_ids'] for row in rows))

    def test_target_and_monitoring_labels_never_enter_fit(self):
        rows = pregame_rows(fixture())
        for target in (2024, 2025, 2026):
            with self.assertRaisesRegex(ValueError, 'cannot enter fitting'):
                fit_model(rows, target)

    def test_delayed_training_label_blocks_fit(self):
        rows = pregame_rows(fixture())[:32]
        rows[0] = {**rows[0], 'label_observed_at': '2024-09-01T00:00:00Z'}
        with self.assertRaisesRegex(ValueError, 'unavailable at fit'):
            fit_model(rows, 2024)


class SourceClosureTests(unittest.TestCase):
    def catalog(self):
        import hashlib
        body = b'{"invented":true,"events":[]}'
        key = hashlib.sha256(body).hexdigest()
        scopes = {name: {'complete': True, 'objects': [{'body_sha256': key, 'request_id': 'original'}]}
                  for name in ('fbs', 'basketball', 'march')}
        return scopes, {key: body}

    def test_duplicates_and_empty_body_are_still_captured(self):
        scopes, bodies = self.catalog()
        result = source_catalog(scopes, scopes, bodies, 'original')
        self.assertEqual(result['request_status'], 'CAPTURED')
        self.assertEqual(result['unique_content_objects'], 1)
        self.assertEqual(result['unique_request_receipts'], 1)
        self.assertFalse(result['may_dispatch'])

    def test_partial_cross_project_listing_never_proves_missing(self):
        scopes, bodies = self.catalog()
        scopes['march']['complete'] = False
        with self.assertRaisesRegex(ValueError, 'partial'):
            source_catalog(scopes, scopes, bodies, 'missing')

    def test_missing_scope_blocks(self):
        scopes, bodies = self.catalog()
        with self.assertRaisesRegex(ValueError, 'all declared'):
            source_catalog(scopes, ('fbs', 'basketball', 'march', 'nfl'), bodies, 'missing')

    def test_raw_hash_tampering_blocks(self):
        scopes, bodies = self.catalog()
        bodies[next(iter(bodies))] += b' '
        with self.assertRaisesRegex(ValueError, 'closure'):
            source_catalog(scopes, scopes, bodies, 'missing')

    def test_scoped_missing_is_not_purchase_authorization(self):
        scopes, bodies = self.catalog()
        result = source_catalog(scopes, scopes, bodies, 'different')
        self.assertEqual(result['request_status'], 'NOT_FOUND_IN_DECLARED_SCOPES')
        self.assertFalse(result['may_dispatch'])


class JournalTests(unittest.TestCase):
    def test_failed_fit_is_preserved_then_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = FitJournal(tmp)
            def failure(): raise ArithmeticError('invented failed fit')
            with self.assertRaises(ArithmeticError): journal.fit('fit_a', {'inputs': 1}, failure)
            model, cached = journal.fit('fit_a', {'inputs': 1}, lambda: {'value': 3})
            self.assertFalse(cached)
            ledger = json.loads(journal.journal.read_text())
            self.assertEqual([x['status'] for x in ledger['attempts']], ['FAILED', 'COMPLETE'])
            self.assertEqual(model['value'], 3)

    def test_interrupted_reservation_never_counts_as_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = FitJournal(tmp)
            atomic_json(journal.journal, {'schema': 'fixture', 'attempts': [
                {'unit': 'fit_a', 'input_identity': digest({'x': 1}), 'status': 'RUNNING', 'attempt': 1}]})
            journal.fit('fit_a', {'x': 1}, lambda: {'value': 2})
            statuses = [x['status'] for x in json.loads(journal.journal.read_text())['attempts']]
            self.assertEqual(statuses, ['INTERRUPTED', 'COMPLETE'])

    def test_changed_inputs_and_corrupt_model_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = FitJournal(tmp)
            journal.fit('fit_a', {'x': 1}, lambda: {'value': 1})
            with self.assertRaisesRegex(ValueError, 'changed input'):
                journal.fit('fit_a', {'x': 2}, lambda: {})
            record = json.loads(journal.journal.read_text())['attempts'][0]
            (Path(tmp) / record['output_path']).write_text('{}')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                journal.fit('fit_a', {'x': 1}, lambda: {})

    def test_concurrent_reentry_produces_one_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = FitJournal(tmp)
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: journal.fit('fit_a', {'x': 1}, lambda: {'value': 1}), range(2)))
            self.assertEqual(sorted(cached for _, cached in results), [False, True])
            self.assertEqual(len(json.loads(journal.journal.read_text())['attempts']), 1)

    def test_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'safe unit'):
                FitJournal(tmp).fit('../outside', {}, lambda: {})

    def test_exact_reentry_does_no_new_fits(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = run_demo(tmp)
            second = run_demo(tmp)
            self.assertEqual((first['new_synthetic_fits'], second['new_synthetic_fits']), (3, 0))
            self.assertEqual(first['results'], second['results'])
            self.assertEqual(second['reused_synthetic_fits'], 3)
            self.assertEqual(first['actual_owner_fits'], 0)
            self.assertFalse(first['2026_used_for_selection'])
            self.assertEqual(first['shared_catalog']['credits_spent'], 0)


if __name__ == '__main__': unittest.main()
