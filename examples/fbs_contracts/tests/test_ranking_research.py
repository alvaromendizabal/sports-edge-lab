"""Ranking metadata must preserve clocks, missingness and the selected-model boundary."""
from pathlib import Path
import shutil
import subprocess
import unittest

class RankingResearchTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node required for presentation contracts')
    def test_clock_and_publication_boundaries(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('test_ranking_research_logic.cjs'))], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == '__main__':
    unittest.main()
