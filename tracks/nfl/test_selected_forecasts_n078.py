"""Protect authenticated values, temporal claims and unequal evidence denominators."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
import selected_review_n078 as review

ROOT=Path(__file__).parent


class N078SelectedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(ROOT/review.FORECAST).read_bytes()
        cls.health=json.loads((ROOT/review.HEALTH).read_bytes())
        cls.value=json.loads(cls.raw)

    def mutate(self,change):
        value=copy.deepcopy(self.value);change(value)
        raw=json.dumps(value).encode();health=copy.deepcopy(self.health)
        health['selected_forecasts_sha256']=hashlib.sha256(raw).hexdigest()
        return raw,health

    def test_exact_source_and_all_game_coverage(self):
        value=review.validate(self.raw,self.health)
        self.assertEqual(value['counts']['schedule_games'],272)
        self.assertEqual(value['counts']['current_selected_rows'],448)
        self.assertEqual(value['counts']['current_selected_games'],112)
        self.assertEqual(value['counts']['official_time_tbd_games'],24)
        available={r['role_id'] for g in value['games'] for t in g['targets'].values() for r in t['roles'] if r['current_forecast_available'] and r['role_id'].startswith('primary_')}
        self.assertEqual(available,{'primary_total_crps_h3600s'})
        self.assertEqual(self.health['owner_return_sha256'],'3d373e6ed9959039f22fd78f3c00b6ecb9c673c2c0189c21aeeef8189cf5f8c9')

    def test_forecast_body_changed_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'ORIGINAL_BYTES_CHANGED'):
            review.validate(self.raw+b' ',self.health)

    def test_postgame_issue_cannot_become_forward(self):
        def change(v):
            g=next(g for g in v['games'] if g['targets']['win']['current_forecasts'])
            g['targets']['win']['current_forecasts'][0]['original_issue_at_utc']=g['kickoff_utc']
        with self.assertRaisesRegex(ValueError,'CLOCK_INVALID'):
            review.validate(*self.mutate(change))

    def test_reconstruction_cannot_acquire_original_clock(self):
        def change(v):
            g=next(g for g in v['games'] if g['targets']['win']['prior_selected_reconstruction'])
            g['targets']['win']['prior_selected_reconstruction'][0]['original_issue_at_utc']='2026-01-01T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError,'RECONSTRUCTION_ORIGINAL'):
            review.validate(*self.mutate(change))

    def test_duplicate_game_rejected(self):
        def change(v):v['games'][1]['game_id']=v['games'][0]['game_id']
        with self.assertRaisesRegex(ValueError,'GAME_DENOMINATOR'):
            review.validate(*self.mutate(change))

    def test_tbd_placeholder_rejected(self):
        def change(v):
            next(g for g in v['games'] if g['official_time_tbd'])['kickoff_utc']='2026-12-01T00:00:00+00:00'
        with self.assertRaisesRegex(ValueError,'TBD_PLACEHOLDER'):
            review.validate(*self.mutate(change))

    def test_135_rows_cannot_become_135_games(self):
        h=copy.deepcopy(self.health);h['forward_monitor_unique_games']=135
        with self.assertRaisesRegex(ValueError,'EARLY_MONITOR_DENOMINATOR'):
            review.validate(self.raw,h)

    def test_exposed_early_monitor_cannot_promote(self):
        h=copy.deepcopy(self.health);h['forward_monitor_scorecards'][0]['current_season_selection_eligible']=True
        with self.assertRaisesRegex(ValueError,'EARLY_MONITOR_SELECTION'):
            review.validate(self.raw,h)

    def test_source_captures_are_not_admitted_benchmarks(self):
        providers=self.health['provider_coverage']
        self.assertEqual([p['provider'] for p in providers],['DraftKings','Kalshi','Polymarket'])
        self.assertTrue(all(p['captured_games'] is None and p['qualified_comparison_cells']==0 for p in providers))
        self.assertEqual(self.health['forward_monitor_rows'],15*3*3)

    def test_reopened_html_is_exact_and_offline(self):
        page=review.render(self.raw,self.health)
        self.assertEqual((ROOT/'season_review_n078.html').read_text(),page)
        self.assertNotIn('<script src=',page)


if __name__=='__main__':unittest.main()
