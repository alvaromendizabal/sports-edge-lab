"""Content identity and complete two-snapshot transport, without scientific credit."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from examples.ncaa_review.public_shared_status import build


class SharedStatusTests(unittest.TestCase):
    def fixture(self, root):
        body = gzip.compress(b'{"fixture":true}\n', mtime=0)
        sha = hashlib.sha256(body).hexdigest()
        for index, name in enumerate(("population", "population_r17")):
            folder = root / name
            (folder / "status").mkdir(parents=True)
            filename = f"snapshot_{index}.jsonl.gz"
            (folder / "status" / filename).write_bytes(body)
            pin = {"filename": filename, "sha256": sha, "bytes": len(body), "rows": 1, "population_hash": str(index) * 64, "codec": "jsonl_gzip", "scope": "EXPLICIT_CELLS_NO_SPARSE_DEFAULTS", "physical_readback_verified": True}
            (folder / "population_public.json").write_text(json.dumps({"schema": "sel.ncaa.b088.population_public.v1", "population_hash": str(index) * 64, "status_partition_manifest": [pin]}))
        return body, sha

    def test_exact_shared_bytes_and_preserved_snapshot_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            body, sha = self.fixture(root)
            before = {name: (root / name / "population_public.json").read_bytes() for name in ("population", "population_r17")}
            receipt = build(root, reconstruct=False)
            self.assertEqual((receipt["logical_partition_references"], receipt["physical_objects"]), (2, 1))
            self.assertEqual(receipt["duplicated_bytes_avoided"], len(body))
            self.assertEqual((root / "status_objects" / f"{sha}.jsonl.gz").read_bytes(), body)
            self.assertEqual(len(receipt["objects"][0]["references"]), 2)
            self.assertEqual(build(root, reconstruct=False), receipt)
            for name, original in before.items():
                self.assertEqual((root / name / "population_public.json").read_bytes(), original)

    def test_corrupt_existing_object_is_preserved_and_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, sha = self.fixture(root)
            build(root, reconstruct=False)
            path = root / "status_objects" / f"{sha}.jsonl.gz"
            path.write_bytes(b"corrupt-existing-object")
            with self.assertRaisesRegex(ValueError, "EXISTING_PUBLIC_ASSET_CONFLICT"):
                build(root, reconstruct=False)
            self.assertEqual(path.read_bytes(), b"corrupt-existing-object")

    def test_missing_source_partition_cannot_claim_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            (root / "population_r17/status/snapshot_1.jsonl.gz").unlink()
            with self.assertRaises(FileNotFoundError):
                build(root, reconstruct=False)
            self.assertFalse((root / "status_objects_manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
