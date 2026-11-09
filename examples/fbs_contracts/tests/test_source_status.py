"""Exact dated period routing and metadata-only source associations."""
from pathlib import Path
import shutil,subprocess,unittest
class SourceStatusTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node required for source/period contracts')
    def test_metadata_identity_and_week_transition_guards(self):
        result=subprocess.run(['node','--test',str(Path(__file__).with_name('test_source_status_logic.cjs'))],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
if __name__=='__main__':unittest.main()
