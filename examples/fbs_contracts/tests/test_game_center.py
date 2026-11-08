"""Source-preserving game-center and matched-cohort presentation contracts."""
from pathlib import Path
import shutil
import subprocess
import unittest


class GameCenterTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node required for presentation guards')
    def test_fixture_order_intervals_family_scope_and_recorded_pairs(self):
        result=subprocess.run(['node','--test',str(Path(__file__).with_name('test_game_center_logic.cjs'))],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
