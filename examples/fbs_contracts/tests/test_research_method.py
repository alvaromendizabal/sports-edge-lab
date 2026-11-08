"""Dated week boundaries and forecast-age display must not imply issuance."""
from pathlib import Path
import shutil
import subprocess
import unittest


class ResearchMethodTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node required for presentation contracts')
    def test_week_age_and_issuance_boundaries(self):
        result=subprocess.run(['node','--test',str(Path(__file__).with_name('test_research_method_logic.cjs'))],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__': unittest.main()
