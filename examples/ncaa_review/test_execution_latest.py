"""Latest real invocation scope, preservation and public rendering guards."""
from copy import deepcopy
from pathlib import Path
import base64
import hashlib
import json
import re
import unittest

import execution_latest_r32 as latest


class LatestExecutionTests(unittest.TestCase):
    def setUp(self):
        self.data = latest.load()

    def rejected(self, change):
        candidate = deepcopy(self.data)
        change(candidate)
        with self.assertRaises((ValueError,KeyError)):
            latest.validate(candidate)

    def test_actual_three_failures_are_not_one_run_or_success(self):
        self.assertEqual(self.data['tally']['failed_owner_executions'],3)
        self.assertEqual(self.data['tally']['distinct_run_ids'],1)
        self.assertEqual(len({r['manifest_sha256'] for r in self.data['invocations']}),3)
        self.rejected(lambda d:d['tally'].update(successful_owner_executions=1))
        self.rejected(lambda d:d['tally'].update(distinct_run_ids=3))

    def test_duplicate_manifest_cannot_hide_a_separate_invocation(self):
        self.rejected(lambda d:d['invocations'][1].update(manifest_sha256=d['invocations'][0]['manifest_sha256']))

    def test_saved_fits_and_stage_fixtures_cannot_become_current_work(self):
        for key in ('new_owner_fits','new_stages_completed','completed_stages_reused'):
            self.rejected(lambda d,key=key:d['invocations'][0].update({key:1}))
        self.rejected(lambda d:d['tally'].update(historical_checkpoints_reused_in_these_invocations=108))

    def test_requested_cpus_do_not_certify_fitting_workers(self):
        self.rejected(lambda d:d['invocations'][0].update(peak_scientific_workers=36))
        self.rejected(lambda d:d['invocations'][0].update(peak_measured_owner_cores=36))

    def test_unchanged_36_fit_catalog_does_not_gain_sustained_cpu_credit(self):
        self.rejected(lambda d:d['preserved_bounded_acceptance'].update(sustained_180_second_75_percent_gate_certified=True))
        self.rejected(lambda d:d['preserved_bounded_acceptance'].update(peak_real_estimator_kernel_overlap=36))
        self.rejected(lambda d:d['tally'].update(saved_acceptance_fits_refitted=36))

    def test_pointer_restoration_does_not_promote_failed_science(self):
        self.rejected(lambda d:d['discovery_repair'].update(scientific_status='COMPLETE'))
        self.rejected(lambda d:d['discovery_repair'].update(complete_pointer_written=True))

    def test_r33_preparation_cannot_inherit_r32_gate_or_owner_credit(self):
        self.rejected(lambda d:d['next_preparation'].update(owner_executions=1))
        self.rejected(lambda d:d['next_preparation'].update(canonical_source={'bytes':1,'sha256':d['source_sha256']}))
        self.rejected(lambda d:d['next_preparation'].update(status='PREPARED_VERIFIED',upload_verified=False))

    def test_summary_terminal_and_observed_clocks_remain_distinct(self):
        self.rejected(lambda d:d.update(terminal_completed_at=d['invocations'][-1]['started_at']))
        self.rejected(lambda d:d['invocations'][1].update(started_at=d['invocations'][0]['started_at']))

    def test_measured_cost_is_not_invoice_or_exclusive_owner_allocation(self):
        self.rejected(lambda d:d['cost'].update(invoice=True))
        self.rejected(lambda d:d['cost'].update(exclusive_owner_allocation=True))
        self.rejected(lambda d:d['invocations'][0].update(estimated_instance_wall_cost_usd=200))

    def test_scientific_and_public_boundaries_stay_unchanged(self):
        self.rejected(lambda d:d['science_contract'].update(test_selection_weight=.5))
        self.rejected(lambda d:d['publication'].update(new_fits=36))
        self.rejected(lambda d:d['failure'].update(explanation='s3://private/example'))
        self.rejected(lambda d:d.update(unknown_claim=True))

    def test_static_panel_has_exact_latest_evidence_download(self):
        html=latest.render_panel(self.data)
        encoded=re.search(r'download="ncaa-latest-execution.json" href="data:application/json;base64,([^"]+)"',html).group(1)
        self.assertEqual(json.loads(base64.b64decode(encoded)),self.data)
        self.assertEqual(html.count('<tr>'),4)
        self.assertIn('0 / 3',html)
        self.assertIn('180-second, 75% sustained utilization gate remains uncertified',html)
        for row in self.data['invocations']:
            self.assertIn(row['manifest_sha256'],html)

    def test_current_banner_changes_no_historical_science(self):
        from v12_public_status import strip_banner,render_banner
        index=Path(__file__).resolve().parents[2]/'docs/ncaa/index.html'
        body=strip_banner(index.read_text())
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),'26fdce5b2c4ffd27debdcfda835d6a459e3f4a2de4edac9bf077d68e1bf3392a')
        self.assertEqual(strip_banner(render_banner(index.read_text())),body)


if __name__=='__main__':
    unittest.main()
