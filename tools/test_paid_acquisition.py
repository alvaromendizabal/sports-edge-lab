"""Offline integration checks: no AWS credentials or outbound HTTP required."""
import collections
import io
import json
import threading
import time
import types
import unittest
import urllib.error

from acquire_paid_data import Archive, Budget, BudgetStop, digest, blob


class FakeS3:
    class exceptions:
        class NoSuchKey(Exception):
            pass

    def __init__(self):
        self.objects = {}

    def get_object(self, Bucket, Key):
        if Key not in self.objects:
            raise self.exceptions.NoSuchKey()
        return {"Body": io.BytesIO(self.objects[Key])}

    def put_object(self, Bucket, Key, Body, **kwargs):
        self.objects[Key] = Body

    def upload_fileobj(self, Fileobj, Bucket, Key, **kwargs):
        self.objects[Key] = Fileobj.read()


class Response(io.BytesIO):
    status = 200
    headers = {"x-requests-last": "30", "x-requests-used": "30", "x-requests-remaining": "4999970"}


class Opener:
    def __init__(self, raw):
        self.raw = raw
        self.calls = 0

    def open(self, req, timeout):
        self.calls += 1
        return Response(self.raw)


def archive(raw):
    obj = Archive.__new__(Archive)
    obj.args = types.SimpleNamespace(bucket="test", max_response_mb=1)
    obj.deadline = time.monotonic() + 10
    obj.run_id = "offline-test"
    obj.s3 = FakeS3()
    obj.keys = {"odds": "synthetic-test-credential"}
    obj.opener = Opener(raw)
    obj.budget = Budget(120, 10)
    obj.lock = threading.Lock()
    obj.stats = collections.Counter()
    obj.receipts = []
    obj.failures = []
    obj.stop = threading.Event()
    obj.cache = {}
    obj.request_locks = collections.defaultdict(threading.Lock)
    obj.blocked_endpoints = set()
    obj.coverage = collections.Counter()
    return obj


class Integration(unittest.TestCase):
    def test_success_then_cache_verifies_raw_hash_and_no_secret_saved(self):
        obj = archive(b'{"data":[{"id":"one"}]}')
        args = ("odds", "nfl", "/v4/historical/sports/americanfootball_nfl/odds", {"date": "2025-01-01T00:00:00Z"}, "test")
        first = obj.capture(*args)
        obj.cache.clear()  # Simulate a fresh process that has only remote cache.
        second = obj.capture(*args)
        self.assertEqual(first, second)
        self.assertEqual(obj.opener.calls, 1)
        self.assertEqual(obj.budget.snapshot()["actual_known"]["odds"], 30)
        self.assertTrue(all(b"synthetic-test-credential" not in data for data in obj.s3.objects.values()))
        receipt = next(iter(obj.cache.values()))
        obj.s3.objects[receipt["raw_key"]] = __import__("gzip").compress(b'{"data":[]}')
        with self.assertRaises(RuntimeError):
            obj.capture(*args)

    def test_error_body_secret_not_saved_and_provider_stops(self):
        obj = archive(b"")
        class ErrorOpener:
            def open(self, req, timeout):
                raise urllib.error.HTTPError(req.full_url, 401, "invalid key synthetic-test-credential", {}, io.BytesIO(b"synthetic-test-credential"))
        obj.opener = ErrorOpener()
        with self.assertRaises(BudgetStop):
            obj.capture("odds", "nfl", "/odds", {}, "test")
        self.assertTrue(all(b"synthetic-test-credential" not in data for data in obj.s3.objects.values()))
        self.assertFalse(any("request-index" in key for key in obj.s3.objects))
        self.assertIn("odds", obj.budget.snapshot()["disabled_providers"])

    def test_credential_echo_is_never_persisted(self):
        obj = archive(b'{"error":"synthetic-test-credential"}')
        with self.assertRaises(RuntimeError):
            obj.capture("odds", "nfl", "/odds", {}, "test")
        self.assertEqual(obj.s3.objects, {})


if __name__ == "__main__":
    unittest.main()
