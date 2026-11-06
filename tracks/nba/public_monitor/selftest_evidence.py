"""Named unittest diagnostics for invented, credential-free examples.

The caller receives evidence even when class setup fails before a test starts.
This module does not authorize, execute or attest to any research owner run.
"""
from __future__ import annotations

import io
import unittest


class NamedResult(unittest.TextTestResult):
    """Keep class/loader failures separate from previously completed tests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
        self.active = None
        self.fixture_records = {}

    def _record(self, test):
        identity = test.id()
        if self.active is not None and self.active["id"] == identity:
            return self.active
        if identity not in self.fixture_records:
            record = {"id": identity, "status": "RUNNING", "without_startTest": True}
            self.fixture_records[identity] = record
            self.records.append(record)
        return self.fixture_records[identity]

    def startTest(self, test):
        self.active = {"id": test.id(), "status": "RUNNING"}
        self.records.append(self.active)
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        self.active = None

    def addSuccess(self, test):
        self._record(test)["status"] = "PASS"
        super().addSuccess(test)

    def addFailure(self, test, error):
        self._record(test)["status"] = "FAIL"
        super().addFailure(test, error)

    def addError(self, test, error):
        self._record(test)["status"] = "ERROR"
        super().addError(test, error)

    def addSkip(self, test, reason):
        self._record(test).update(status="SKIP", reason=str(reason))
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, error):
        self._record(test)["status"] = "EXPECTED_FAILURE"
        super().addExpectedFailure(test, error)

    def addUnexpectedSuccess(self, test):
        self._record(test)["status"] = "UNEXPECTED_SUCCESS"
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, error):
        if error is not None:
            self._record(test)["status"] = (
                "FAIL" if issubclass(error[0], test.failureException) else "ERROR")
        super().addSubTest(test, subtest, error)


def inspect_suite(suite):
    """Return named evidence; only a nonempty all-PASS suite satisfies the gate.

    Class errors can make the number of records exceed testsRun. These counts
    deliberately remain separate. The caller decides where to retain the report
    and full log; this function has no filesystem or network side effects.
    """
    stream = io.StringIO()
    result = unittest.TextTestRunner(
        stream=stream, verbosity=2, resultclass=NamedResult).run(suite)
    passed = (result.testsRun > 0 and result.wasSuccessful()
              and not result.skipped and not result.expectedFailures
              and all(record["status"] == "PASS" for record in result.records))
    return {"status": "PASS" if passed else "FAILED", "tests_run": result.testsRun,
            "failures": len(result.failures), "errors": len(result.errors),
            "skipped": len(result.skipped), "expected_failures": len(result.expectedFailures),
            "unexpected_successes": len(result.unexpectedSuccesses), "records": result.records,
            "failed_test_details": [{"id": test.id(), "traceback": detail}
                                    for test, detail in result.failures + result.errors],
            "log": stream.getvalue(), "owner_completion_asserted": False}
