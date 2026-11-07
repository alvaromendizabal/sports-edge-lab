"""Run the presentation's numeric/identity failure cases without a browser."""
from pathlib import Path
import shutil
import subprocess
import unittest


class DiagnosticsLogicTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is required for the browser-independent diagnostics')
    def test_numeric_and_cohort_admission(self):
        path = Path(__file__).with_name('test_diagnostics_logic.cjs')
        result = subprocess.run(['node', '--test', str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
