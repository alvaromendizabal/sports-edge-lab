import shutil
import subprocess
import unittest
from pathlib import Path


class ForwardOutlookPresentationContracts(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is required for presentation contracts')
    def test_identity_horizon_partial_coverage_and_metadata_exports(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('test_forward_outlooks_logic.cjs'))], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
