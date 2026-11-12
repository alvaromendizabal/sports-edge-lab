"""Guard actual-run status, selected issue clocks and full-precision monitoring."""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

import recovery_dashboard as dashboard


class RecoveryDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.raw = dashboard.load_payload()

    def test_selected_role_population_and_display_precision(self):
        self.assertEqual(len(self.data['selected_originals']), 90)
        self.assertEqual(self.data['selected_recovery']['projected_public_issue_rows_after_merge'], 232)
        self.assertEqual({target: sum(r['target'] == target for r in self.data['selected_originals'])
                          for target in ('win', 'margin', 'total')}, {'win': 30, 'margin': 30, 'total': 30})
        self.assertFalse(self.data['selected_recovery']['source_current_outcomes_used_for_selection'])

    def test_failed_owner_cannot_become_scientific_success(self):
        for key, value in [('new_verified_fits', 1), ('runtime_verified_reused_fits', 1),
                           ('new_issues', 1), ('promotions', 1), ('science_started', True),
                           ('actual_owner_parallel_benchmark_reached', True), ('actual_startup_lease_cpus', 12)]:
            with self.subTest(key=key):
                data=copy.deepcopy(self.data);data['actual_owner'][key]=value
                with self.assertRaises(ValueError): dashboard.validate(data)
        for key, value in [('complete_current_season_coverage', True), ('verified_new_upcoming_forecasts', 1)]:
            data=copy.deepcopy(self.data);data[key]=value
            with self.assertRaises(ValueError): dashboard.validate(data)

    def test_original_clocks_outcomes_and_role_scope_fail_closed(self):
        for key, value in [('server_last_modified_utc', '2030-01-01T00:00:00+00:00'),
                           ('actual', 1), ('automatic_promotion', True), ('selection_scope', 'candidate_grid'),
                           ('new_B063_issue_credit', 1), ('durable_issued_before_cutoff', False)]:
            with self.subTest(key=key):
                data=copy.deepcopy(self.data);data['selected_originals'][0][key]=value
                with self.assertRaises(ValueError): dashboard.validate(data)
        data=copy.deepcopy(self.data)
        data['selected_originals'][0]['server_last_modified_utc']=data['selected_originals'][0]['cutoff_time']
        with self.assertRaises(ValueError): dashboard.validate(data)

    def test_postissue_metrics_are_pinned_full_precision_and_separate(self):
        monitor=self.data['late_monitor']
        self.assertEqual(len(monitor['metrics']), 11);self.assertEqual(len(monitor['outcomes']), 8)
        ridge=next(r for r in monitor['metrics'] if r['public_model_id']=='frozen-component-ncaam-margin-2cf81b3e')
        self.assertEqual(ridge['mae'], 14.686754186948141)
        self.assertNotEqual(round(ridge['mae'], 6), 14.686833)
        for mutation in ('rounded_precision', 'metric', 'final', 'promotion'):
            data=copy.deepcopy(self.data)
            if mutation=='rounded_precision':data['late_monitor']['prediction_precision_basis']='ROUNDED_PUBLIC_VALUES'
            elif mutation=='metric':data['late_monitor']['metrics'][0]['mae']=0
            elif mutation=='final':data['late_monitor']['outcomes'][0]['actual_home_points']=100
            else:data['late_monitor']['promotions']=1
            with self.assertRaises(ValueError):dashboard.validate(data)

    def test_new_panel_preserves_every_previous_page_byte(self):
        path=dashboard.HERE.parents[1]/'docs/ncaa/index.html'
        text=path.read_text()
        start=text.index(dashboard.START);end=text.index(dashboard.END)+len(dashboard.END)
        previous=text[:start]+text[end:]
        self.assertEqual(hashlib.sha256(previous.encode()).hexdigest(),
                         'acc635d3362312c5f395c2fc296e3eaa382ef6fc8743e437b4ee7bfd0238451f')
        self.assertEqual(dashboard.render(previous),text)
        self.assertEqual(dashboard.render(text),text)
        old=json.loads(re.search(r'<script id="terminal-data" type="application/json">(.*?)</script>',text,re.S).group(1))
        self.assertEqual(old,json.loads((dashboard.HERE/'B063_TERMINAL_PUBLIC_DATA.json').read_text()))

    def test_public_boundary_and_embedded_payload(self):
        for marker in ('s3://','sagemaker-user','arn:aws:','recipe_id','feature_columns','model_weights','access_key','secret_key'):
            self.assertNotIn(marker,self.raw)
        page=dashboard.render('<html><body><main><p>Preserved result</p></main></body></html>')
        self.assertIn('Preserved result',page)
        self.assertNotIn('__RECOVERY_DATA__',page)
        self.assertNotRegex(page,r'<script[^>]+src=')
        self.assertEqual(json.loads(re.search(r'<script id="b063r1-data" type="application/json">(.*?)</script>',page,re.S).group(1)),self.data)


if __name__=='__main__':unittest.main()
