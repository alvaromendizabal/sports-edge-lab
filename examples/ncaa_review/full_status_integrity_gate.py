"""Exhaustive NCAA public-status gate, run by the existing longer browser CI job.

This retains the full all-payload/all-row verification outside the shared
three-minute Python job. It does not skip, sample, or transform evidence.
"""
import gzip
import hashlib
import json
import re
import unittest

from examples.ncaa_review.public_status_transport import unpack
from examples.ncaa_review.test_three_season_public import CELL_KEYS, PRIVATE_BYTE_MARKERS, POP


class CompletePublicStatusIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        unpack(POP)
        cls.data = json.loads((POP / "population_public.json").read_text())
        cls.manifest = json.loads((POP / "status_manifest.json").read_text())

    def test_complete_physical_status_projection(self):
        self.assertEqual(self.manifest["population_hash"], self.data["population_hash"])
        self.assertIs(self.manifest["complete"], True)
        expected = {p["filename"]: p for p in self.data["status_partition_manifest"]}
        self.assertEqual(len(expected), len(self.manifest["parts"]))
        self.assertEqual(expected, {p["filename"]: p for p in self.manifest["parts"]})
        total = 0
        for descriptor in self.manifest["parts"]:
            filename = descriptor["filename"]
            self.assertRegex(filename, r"^[A-Za-z0-9_-]+\.jsonl\.gz$")
            body = (POP / "status" / filename).read_bytes()
            self.assertEqual(len(body), descriptor["bytes"])
            self.assertEqual(hashlib.sha256(body).hexdigest(), descriptor["sha256"])
            logical = gzip.decompress(body)
            self.assertEqual(len(logical), descriptor["logical_bytes"])
            self.assertEqual(hashlib.sha256(logical).hexdigest(), descriptor["logical_sha256"])
            self.assertLessEqual(len(logical), 2 << 20)
            lines = logical.splitlines()
            self.assertEqual(len(lines), descriptor["rows"])
            self.assertLessEqual(len(lines), 4096)
            self.assertEqual(descriptor["scope"], "EXPLICIT_CELLS_NO_SPARSE_DEFAULTS")
            # Inspect actual decoded status bytes once. Encoded source-pack strings
            # are transport bytes and are never mistaken for rendered content.
            lowered = logical.lower()
            for marker in PRIVATE_BYTE_MARKERS + [bytes([99, 105, 114, 99, 97])]:
                if marker in lowered:
                    self.fail(f"Private/public-scope marker in {filename}")
            if b"akia" in lowered:
                self.assertIsNone(re.search(rb"\bAKIA[A-Z0-9]{16}\b", logical))
            for line in lines:
                row = json.loads(line)
                if set(row) != CELL_KEYS or row["league"] != descriptor["league"] or row["season_end_year"] != descriptor["season_end_year"] or row["target"] != descriptor["target"]:
                    self.fail(f"Invalid explicit public status cell in {filename}")
            total += len(lines)
        self.assertEqual(total, self.manifest["rows"])
        self.assertEqual(total, self.data["status_ledger_rows"])

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CompletePublicStatusIntegrity)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    manifest = json.loads((POP / "status_manifest.json").read_text())
    print(json.dumps({"status": "PASS", "parts": len(manifest["parts"]),
        "explicit_status_cells": manifest["rows"],
        "logical_bytes": sum(p["logical_bytes"] for p in manifest["parts"]),
        "all_payload_hashes_and_readback": True, "all_row_allowlists": True,
        "all_decoded_bytes_privacy_checked": True, "sampling_used": False}))
