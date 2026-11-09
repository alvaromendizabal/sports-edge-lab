import shutil
import subprocess
import unittest
from pathlib import Path


class ForecastEvidencePresentationContracts(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is required for presentation tests')
    def test_original_metrics_and_explicit_gaps(self):
        script=Path(__file__).with_name('test_forecast_evidence_logic.cjs')
        result=subprocess.run(['node','--test',str(script)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':
    unittest.main()
