"""Small transport fixtures; no production predictions or model fits."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from examples.ncaa_review.public_status_transport import pack, unpack


class PublicStatusTransportTests(unittest.TestCase):
    def fixture(self, root):
        original = root / "original"
        original.mkdir()
        population = root / "population"
        population.mkdir()
        parts = []
        for index in range(3):
            body = gzip.compress((json.dumps({"fixture": index}) + "\n").encode(), mtime=0)
            filename = f"fixture_{index}.jsonl.gz"
            (original / filename).write_bytes(body)
            parts.append({"filename": filename, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "population_hash": "a" * 64, "codec": "jsonl_gzip", "scope": "EXPLICIT_CELLS_NO_SPARSE_DEFAULTS", "physical_readback_verified": True})
        data = {"schema": "sel.ncaa.b088.population_public.v1", "population_hash": "a" * 64, "status_partition_manifest": parts, "status_ledger_rows": 3}
        source = population / "population_public.json"
        source.write_text(json.dumps(data) + "\n")
        manifest = pack(source, original, population / "source_packs", max_pack_bytes=700)
        return population, original, manifest

    def test_exact_reassembly_and_warm_identical_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            population, original, manifest = self.fixture(Path(directory))
            self.assertGreater(len(manifest["packs"]), 1)
            cold, warm = unpack(population), unpack(population)
            self.assertEqual((cold["created"], warm["created"], warm["reused_identical"]), (3, 0, 3))
            self.assertFalse(cold["private_tables_included"])
            for file in original.iterdir():
                self.assertEqual(file.read_bytes(), (population / "status" / file.name).read_bytes())

    def test_missing_pack_cannot_claim_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            population, _, manifest = self.fixture(Path(directory))
            (population / "source_packs" / manifest["packs"][-1]["filename"]).unlink()
            with self.assertRaisesRegex(ValueError, "MISSING_OR_UNSAFE"):
                unpack(population)

    def test_corrupt_pack_and_changed_population_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            population, _, manifest = self.fixture(Path(directory))
            file = population / "source_packs" / manifest["packs"][0]["filename"]
            file.write_bytes(file.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "BYTES_OR_HASH_MISMATCH"):
                unpack(population)
            public = population / "population_public.json"
            public.write_bytes(public.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "MANIFEST_IDENTITY_MISMATCH"):
                unpack(population)

    def test_existing_conflict_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            population, _, _ = self.fixture(Path(directory))
            output = population / "status"
            output.mkdir()
            file = output / "fixture_0.jsonl.gz"
            file.write_bytes(b"existing-conflicting-evidence")
            with self.assertRaisesRegex(ValueError, "EXISTING_PUBLIC_ASSET_CONFLICT"):
                unpack(population)
            self.assertEqual(file.read_bytes(), b"existing-conflicting-evidence")


if __name__ == "__main__":
    unittest.main()
