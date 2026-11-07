"""Run target-accounting regressions against synthetic and retained public rows."""
from pathlib import Path
import shutil
import subprocess
import unittest


class CoverageLogicTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is required for display accounting')
    def test_missing_targets_are_not_hidden_by_other_predictions(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('test_coverage_logic.cjs'))], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
