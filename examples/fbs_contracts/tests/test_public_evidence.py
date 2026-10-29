import json
from pathlib import Path
import unittest
from examples.fbs_contracts.build_review import OUTPUT, ROOT, evidence, render


class PublicEvidenceTests(unittest.TestCase):
    def test_owner_failure_never_increments_completed_fit_count(self):
        value = evidence()
        self.assertEqual(value['latest_owner_attempt']['status'], 'FAILED')
        self.assertEqual(value['latest_owner_attempt']['new_real_fits'], 0)
        self.assertEqual(value['last_completed_science']['fbs_recent_completed_fits'], 18)
        self.assertEqual(value['prepared_program']['completed_owner_fit_units'], 0)
        self.assertIsNone(value['last_completed_science']['all_project_fbs_lifetime_fits'])

    def test_generated_page_matches_evidence_and_invented_execution(self):
        self.assertEqual(OUTPUT.read_text(), render())
        self.assertIn('203 units', OUTPUT.read_text())
        self.assertIn('Wholly invented', (ROOT / 'notebooks/fbs_branch_review.ipynb').read_text())

    def test_public_evidence_contains_no_private_locations_or_individual_quotes(self):
        serialized = json.dumps(evidence())
        for forbidden in ('s3://', '/home/', 'api_key', 'contract_id', 'bucket', 'account_id', 'game_id'):
            self.assertNotIn(forbidden, serialized)
        for year in (2024, 2025, 2026):
            rows = [r for r in evidence()['panels'] if r['season'] == year]
            self.assertEqual(len(rows), 4)
            self.assertEqual(len({r['games'] for r in rows}), 1)

    def test_notebook_sources_keep_monitoring_and_reentry_assertions(self):
        notebook = json.loads((ROOT / 'notebooks/fbs_branch_review.ipynb').read_text())
        source = '\n'.join(''.join(cell['source']) for cell in notebook['cells'])
        self.assertIn('second["new_synthetic_fits"] == 0', source)
        self.assertIn('not first["2026_used_for_selection"]', source)
        self.assertIn('FBS_PUBLIC_NOTEBOOK_VERIFIED', source)


if __name__ == '__main__': unittest.main()
