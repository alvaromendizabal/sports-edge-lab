"""Failure cases for the invented bounded output contract."""
import copy
import hashlib
import json
import unittest

from tracks.nba.public_monitor.bounded_checkpoint import publish_records, restore_records


class Store:
    def __init__(self):
        self.objects = {}
        self.puts = []
        self.gets = []
        self.fail_put = None
        self.corrupt_get = None

    def put_create_only(self, key, raw):
        if len(self.puts) == self.fail_put:
            raise OSError("invented publication failure")
        self.puts.append(key)
        if key in self.objects and self.objects[key] != raw:
            raise ValueError("create-only conflict")
        self.objects.setdefault(key, raw)

    def get_full(self, key):
        self.gets.append(key)
        raw = self.objects[key]
        return raw + b"!" if key == self.corrupt_get else raw


class BoundedCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.remote = Store()
        self.rows = [{"event": f"invented-2035-{i}", "value": i} for i in range(40)]
        self.options = {"max_shard_bytes": 100}

    def publish(self, rows=None):
        return publish_records(self.rows if rows is None else rows,
                               self.remote, **self.options)

    def restore(self, ref):
        return restore_records(ref, self.remote, **self.options)

    def mutate_manifest(self, ref, mutate):
        doc = json.loads(self.remote.objects[ref["sha256"]])
        mutate(doc)
        raw = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()
        key = hashlib.sha256(raw).hexdigest()
        self.remote.objects[key] = raw
        return {"sha256": key, "bytes": len(raw)}

    def test_many_bounded_shards_restore_exact_sequence(self):
        ref = self.publish()
        self.assertEqual(self.restore(ref), self.rows)
        m = json.loads(self.remote.objects[ref["sha256"]])
        self.assertGreater(len(m["shards"]), 1)
        self.assertTrue(all(x["bytes"] <= 100 for x in m["shards"]))
        self.assertEqual(ref["new_computation_credit"], 0)
        self.assertFalse(ref["producer_invoked"])

    def test_empty_output_is_a_verified_empty_sequence(self):
        self.assertEqual(self.restore(self.publish([])), [])

    def test_unicode_and_embedded_newlines_preserve_values(self):
        rows = [{"text": "é\n東京", "empty": None, "flag": False}]
        self.assertEqual(self.restore(self.publish(rows)), rows)

    def test_single_oversized_record_is_not_silently_split(self):
        with self.assertRaisesRegex(ValueError, "single record"):
            self.publish([{"value": "x" * 101}])
        self.assertEqual(self.remote.puts, [])

    def test_partial_publication_never_returns_commit_reference(self):
        self.remote.fail_put = 2
        with self.assertRaises(OSError):
            self.publish()
        retained = copy.deepcopy(self.remote.objects)
        self.remote.fail_put = None
        ref = self.publish()
        self.assertTrue(all(self.remote.objects[k] == v for k, v in retained.items()))
        self.assertEqual(self.restore(ref), self.rows)

    def test_independent_readback_refuses_corrupt_publication(self):
        original_get = self.remote.get_full
        self.remote.get_full = lambda key: original_get(key) + b"corrupt"
        with self.assertRaisesRegex(ValueError, "independent full readback"):
            self.publish()

    def test_missing_or_changed_shard_refuses_complete_restore(self):
        for kind in ("missing", "changed"):
            self.remote = Store()
            ref = self.publish()
            shard = json.loads(self.remote.objects[ref["sha256"]])["shards"][0]
            if kind == "missing":
                del self.remote.objects[shard["sha256"]]
            else:
                self.remote.objects[shard["sha256"]] += b"!"
            with self.subTest(kind=kind), self.assertRaises((KeyError, ValueError)):
                self.restore(ref)

    def test_wrong_manifest_pin_is_rejected(self):
        ref = self.publish()
        self.remote.objects[ref["sha256"]] += b" "
        with self.assertRaisesRegex(ValueError, "manifest pin"):
            self.restore(ref)

    def test_shard_reordering_cannot_change_sequence(self):
        ref = self.publish()
        changed = self.mutate_manifest(ref, lambda m: m["shards"].reverse())
        with self.assertRaisesRegex(ValueError, "order"):
            self.restore(changed)

    def test_duplicate_or_omitted_descriptor_cannot_pass_closure(self):
        for mutation in (lambda m: m["shards"].append(m["shards"][-1]),
                         lambda m: m["shards"].pop()):
            ref = self.publish()
            changed = self.mutate_manifest(ref, mutation)
            with self.assertRaises(ValueError):
                self.restore(changed)

    def test_equal_shard_bodies_preserve_distinct_sequence_positions(self):
        rows = [{"value": "x" * 60}] * 5
        ref = self.publish(rows)
        m = json.loads(self.remote.objects[ref["sha256"]])
        self.assertEqual(len({s["sha256"] for s in m["shards"]}), 1)
        self.assertEqual(self.restore(ref), rows)

    def test_limits_and_nonfinite_numbers_fail_closed(self):
        with self.assertRaises(ValueError):
            publish_records(self.rows, self.remote, max_shard_bytes=True)
        with self.assertRaises(ValueError):
            self.publish([{"value": float("nan")}])
        with self.assertRaisesRegex(ValueError, "shard count"):
            publish_records(self.rows, self.remote, max_shard_bytes=100, max_shards=1)
        with self.assertRaisesRegex(ValueError, "manifest byte"):
            publish_records([], self.remote, max_manifest_bytes=10)
        ref = self.publish()
        with self.assertRaisesRegex(ValueError, "capacity"):
            restore_records(ref, self.remote, max_total_bytes=10, **self.options)

    def test_extra_manifest_fields_are_not_silently_blessed(self):
        ref = self.publish()
        changed = self.mutate_manifest(ref, lambda m: m.update(extra="unbound"))
        with self.assertRaisesRegex(ValueError, "schema"):
            self.restore(changed)
