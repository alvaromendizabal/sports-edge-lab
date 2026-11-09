import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[3]

class ForecastAccessContracts(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is required for presentation contracts')
    def test_deadlines_missingness_and_target_population(self):
        result=subprocess.run(['node','--test',str(Path(__file__).with_name('test_forecast_access_logic.cjs'))],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_previous_readme_is_byte_preserved(self):
        prior=(ROOT/'docs/fbs/README-history-v050.md').read_bytes()
        expected=json.loads((ROOT/'docs/fbs/execution-status-v051.json').read_text())['prior_readme']
        self.assertEqual(len(prior),expected['bytes'])
        self.assertEqual(hashlib.sha256(prior).hexdigest(),expected['sha256'])

if __name__=='__main__': unittest.main()
