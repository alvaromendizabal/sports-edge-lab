"""Public-package boundary checks; no real data, model fits or provider calls."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import pandas as pd
from common import GateError
from scope_adapter import prepare_inputs


class PublicBoundaryTests(unittest.TestCase):
    def test_private_configuration_is_not_distributed(self):
        folder=Path(__file__).parent
        for name in ['config.json','repair_input_pins.json','source_scope.py','runtime.py']:
            self.assertFalse((folder/name).exists())

    def test_missing_explicit_pins_fails_before_files_are_read(self):
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(Path,'read_text',side_effect=AssertionError('Hidden file read')):
                with self.assertRaises(GateError) as ctx:
                    prepare_inputs(folder,pd.DataFrame())
        self.assertEqual(ctx.exception.category,'SOURCE_STATE')
        self.assertIn('explicit local input pins',str(ctx.exception))

    def test_no_model_weights_or_provider_payloads_in_public_directory(self):
        folder=Path(__file__).parent
        blocked={'.parquet','.pkl','.pickle','.joblib','.pyz','.zip','.csv'}
        self.assertFalse([p.name for p in folder.iterdir() if p.suffix in blocked])
