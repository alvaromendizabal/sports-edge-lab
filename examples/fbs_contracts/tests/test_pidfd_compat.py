"""Local pidfd compatibility checks using only owned, cooperative children."""
from contextlib import contextmanager
import ctypes
import errno
import json
import os
import select
import signal
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

from examples.fbs_contracts import pidfd_compat as compat


@contextmanager
def missing_python_wrappers(*names):
    """Reproduce a Python build that entirely omits selected attributes."""
    modules = {'open': (os, 'pidfd_open'), 'send_signal': (signal, 'pidfd_send_signal')}
    saved = []
    try:
        for name in names:
            module, attribute = modules[name]
            present, value = hasattr(module, attribute), getattr(module, attribute, None)
            saved.append((module, attribute, present, value))
            if present:
                delattr(module, attribute)
        yield
    finally:
        for module, attribute, present, value in reversed(saved):
            if present:
                setattr(module, attribute, value)
            elif hasattr(module, attribute):
                delattr(module, attribute)


class ForeignFunction:
    """An inspectable libc function substitute for deterministic errno checks."""
    def __init__(self, result=0, error=0):
        self.result, self.error = result, error
        self.calls = []
        self.argtypes, self.restype = None, None

    def __call__(self, *arguments):
        self.calls.append(arguments)
        if self.error:
            ctypes.set_errno(self.error)
        return self.result


def fake_library(open_result=123, error=0):
    return SimpleNamespace(pidfd_open=ForeignFunction(open_result, error),
                           pidfd_send_signal=ForeignFunction(-1 if error else 0, error))


@unittest.skipUnless(sys.platform == 'linux', 'The adapter intentionally supports Linux only')
class AdapterContractTests(unittest.TestCase):
    def test_libc_loader_enables_thread_local_errno(self):
        with mock.patch.object(ctypes, 'CDLL') as loader:
            compat._load_libc()
        loader.assert_called_once_with(None, use_errno=True)

    def test_exported_functions_receive_exact_ctypes_prototypes(self):
        library = fake_library()
        with missing_python_wrappers('open', 'send_signal'), mock.patch.object(compat, '_load_libc', return_value=library):
            backend = compat.PidfdBackend()
            self.assertEqual(backend.open(42), 123)
            backend.send_signal(123, 0)
        self.assertEqual(library.pidfd_open.argtypes, [ctypes.c_int, ctypes.c_uint])
        self.assertIs(library.pidfd_open.restype, ctypes.c_int)
        self.assertEqual(library.pidfd_send_signal.argtypes,
                         [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint])
        self.assertIs(library.pidfd_send_signal.restype, ctypes.c_int)
        self.assertEqual(library.pidfd_open.calls, [(42, 0)])
        self.assertEqual(library.pidfd_send_signal.calls, [(123, 0, None, 0)])

    def test_callable_python_functions_are_preferred_independently(self):
        library = fake_library()
        native_open, native_send = mock.Mock(return_value=7), mock.Mock(return_value=None)
        with mock.patch.object(os, 'pidfd_open', native_open, create=True), \
                mock.patch.object(signal, 'pidfd_send_signal', native_send, create=True), \
                mock.patch.object(compat, '_load_libc', return_value=library):
            backend = compat.PidfdBackend()
            backend.open(42)
            backend.send_signal(7, 0)
        self.assertEqual(backend.diagnostics()['selected_backend'], {'open': 'python', 'send_signal': 'python'})
        native_open.assert_called_once_with(42, 0)
        native_send.assert_called_once_with(7, 0, None, 0)
        self.assertEqual(library.pidfd_open.calls, [])
        self.assertEqual(library.pidfd_send_signal.calls, [])

    def test_noncallable_python_attributes_are_not_treated_as_available(self):
        with mock.patch.object(os, 'pidfd_open', None, create=True), \
                mock.patch.object(signal, 'pidfd_send_signal', None, create=True), \
                mock.patch.object(compat, '_load_libc', return_value=fake_library()):
            report = compat.PidfdBackend().diagnostics()
        self.assertTrue(report['python_api']['os_pidfd_open_present'])
        self.assertFalse(report['python_api']['os_pidfd_open_callable'])
        self.assertEqual(report['selected_backend'], {'open': 'libc', 'send_signal': 'libc'})

    def test_native_operational_error_never_retries_using_libc(self):
        library = fake_library()
        rejected = mock.Mock(side_effect=PermissionError(errno.EPERM, 'Invented permission refusal'))
        with mock.patch.object(os, 'pidfd_open', rejected, create=True), \
                mock.patch.object(compat, '_load_libc', return_value=library), \
                mock.patch.object(os, 'kill', side_effect=AssertionError('Numeric PID signaling is forbidden')):
            backend = compat.PidfdBackend()
            with self.assertRaises(OSError) as caught:
                backend.open(42)
        self.assertEqual(caught.exception.errno, errno.EPERM)
        self.assertEqual(library.pidfd_open.calls, [])
        self.assertEqual(backend.diagnostics()['selected_backend']['open'], 'python')

    def test_libc_errno_is_preserved_and_never_redirected(self):
        for number in (errno.ENOSYS, errno.EPERM, errno.ESRCH, errno.EBADF,
                       errno.EINVAL, errno.EMFILE, errno.ENFILE, errno.ENOMEM, errno.ENODEV):
            with self.subTest(errno=number):
                library = fake_library(open_result=-1, error=number)
                with missing_python_wrappers('open', 'send_signal'), \
                        mock.patch.object(compat, '_load_libc', return_value=library), \
                        mock.patch.object(os, 'kill', side_effect=AssertionError('Numeric PID signaling is forbidden')):
                    backend = compat.PidfdBackend()
                    for operation in (lambda: backend.open(42), lambda: backend.send_signal(7, 0)):
                        with self.assertRaises(OSError) as caught:
                            operation()
                        self.assertEqual(caught.exception.errno, number)
                self.assertEqual(len(library.pidfd_open.calls), 1)
                self.assertEqual(len(library.pidfd_send_signal.calls), 1)

    def test_stale_ctypes_errno_is_cleared_before_call(self):
        library = fake_library(open_result=-1)
        with missing_python_wrappers('open', 'send_signal'), mock.patch.object(compat, '_load_libc', return_value=library):
            backend = compat.PidfdBackend()
            ctypes.set_errno(errno.EPERM)
            with self.assertRaises(OSError) as caught:
                backend.open(42)
        self.assertEqual(caught.exception.errno, errno.EIO)

    def test_integer_overflow_and_invalid_target_arguments_never_reach_libc(self):
        library = fake_library()
        with missing_python_wrappers('open', 'send_signal'), mock.patch.object(compat, '_load_libc', return_value=library):
            backend = compat.PidfdBackend()
            for value in (True, 1.5, -1, 0, 2 ** 31, 2 ** 40 + 42):
                with self.subTest(pid=value), self.assertRaises((TypeError, ValueError)):
                    backend.open(value)
            for value in (True, 1.5, -1, 2 ** 31, 2 ** 40 + 7):
                with self.subTest(fd=value), self.assertRaises((TypeError, ValueError)):
                    backend.send_signal(value, 0)
            for value in (True, 1.5, -1, signal.NSIG, 2 ** 31, 2 ** 40):
                with self.subTest(sig=value), self.assertRaises((TypeError, ValueError)):
                    backend.send_signal(7, value)
            for action in (lambda: backend.open(42, 1),
                           lambda: backend.send_signal(7, 0, object(), 0),
                           lambda: backend.send_signal(7, 0, None, 1)):
                with self.assertRaises(ValueError):
                    action()
        self.assertEqual(library.pidfd_open.calls, [])
        self.assertEqual(library.pidfd_send_signal.calls, [])

    def test_invalid_integer_arguments_are_rejected_before_native_calls_too(self):
        native_open, native_send = mock.Mock(), mock.Mock()
        with mock.patch.object(os, 'pidfd_open', native_open, create=True), \
                mock.patch.object(signal, 'pidfd_send_signal', native_send, create=True), \
                mock.patch.object(compat, '_load_libc', return_value=fake_library()):
            backend = compat.PidfdBackend()
            for action in (lambda: backend.open(2 ** 40 + 42),
                           lambda: backend.open(True),
                           lambda: backend.send_signal(2 ** 40 + 7, 0),
                           lambda: backend.send_signal(7, 2 ** 40),
                           lambda: backend.send_signal(7, 1.5)):
                with self.assertRaises((TypeError, ValueError)):
                    action()
        native_open.assert_not_called()
        native_send.assert_not_called()

    def test_missing_python_and_libc_wrappers_report_refusal(self):
        with missing_python_wrappers('open', 'send_signal'), \
                mock.patch.object(compat, '_load_libc', return_value=SimpleNamespace()), \
                mock.patch.object(os, 'kill', side_effect=AssertionError('Numeric PID signaling is forbidden')):
            backend, report = compat.probe_pidfd_support()
            with self.assertRaises(compat.PidfdUnavailable):
                backend.open(42)
        self.assertFalse(report['ready'])
        self.assertFalse(report['available'])
        self.assertEqual(report['selected_backend'], {'open': None, 'send_signal': None})
        self.assertFalse(report['numeric_pid_signal_fallback'])
        self.assertFalse(report['direct_syscalls_used'])
        json.dumps(report, allow_nan=False)

    def test_self_probe_records_exact_failed_operation_and_errno(self):
        library = fake_library(open_result=-1, error=errno.ENOSYS)
        with missing_python_wrappers('open', 'send_signal'), mock.patch.object(compat, '_load_libc', return_value=library):
            _, report = compat.probe_pidfd_support()
        self.assertFalse(report['ready'])
        self.assertEqual(report['probe']['error']['operation'], 'open_self_pidfd')
        self.assertEqual(report['probe']['error']['errno'], errno.ENOSYS)
        self.assertEqual(report['probe']['error']['errno_name'], 'ENOSYS')
        self.assertEqual(library.pidfd_send_signal.calls, [])

    def test_self_probe_closes_its_descriptor_after_send_refusal(self):
        library = fake_library()
        library.pidfd_send_signal = ForeignFunction(-1, errno.EPERM)
        with missing_python_wrappers('open', 'send_signal'), \
                mock.patch.object(compat, '_load_libc', return_value=library), \
                mock.patch.object(os, 'close') as close:
            _, report = compat.probe_pidfd_support()
        close.assert_called_once_with(123)
        self.assertFalse(report['ready'])
        self.assertEqual(report['probe']['error']['operation'], 'signal_zero_self_pidfd')
        self.assertEqual(report['probe']['error']['errno'], errno.EPERM)

    def test_diagnostics_cannot_mutate_selected_backend(self):
        with missing_python_wrappers('open', 'send_signal'), mock.patch.object(compat, '_load_libc', return_value=fake_library()):
            backend = compat.PidfdBackend()
        report = backend.diagnostics()
        report['selected_backend']['send_signal'] = 'numeric'
        report['libc_api']['errors'].append({'invented': True})
        self.assertEqual(backend.diagnostics()['selected_backend']['send_signal'], 'libc')
        self.assertEqual(backend.diagnostics()['libc_api']['errors'], [])

    def test_non_linux_platform_does_not_load_or_use_native_backends(self):
        with mock.patch.object(sys, 'platform', 'unsupported-example'), mock.patch.object(compat, '_load_libc') as load:
            _, report = compat.probe_pidfd_support()
        load.assert_not_called()
        self.assertFalse(report['ready'])
        self.assertEqual(report['selected_backend'], {'open': None, 'send_signal': None})


CHILD = r'''
import signal
import sys

signal.signal(signal.SIGUSR1, lambda *_: print('ACK', flush=True))
signal.alarm(15)
print('READY', flush=True)
for line in sys.stdin:
    if line.strip() == 'EXIT':
        break
'''


@contextmanager
def cooperative_child():
    child = subprocess.Popen([sys.executable, '-u', '-c', CHILD], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        if not select.select([child.stdout], [], [], 5)[0] or child.stdout.readline().strip() != 'READY':
            raise AssertionError('Invented child did not become ready')
        yield child
    finally:
        if child.poll() is None:
            child.stdin.write('EXIT\n')
            child.stdin.flush()
        child.communicate(timeout=5)


@unittest.skipUnless(sys.platform == 'linux', 'Real pidfd checks require Linux')
class RealPidfdTests(unittest.TestCase):
    def ready_backend(self, *missing):
        with missing_python_wrappers(*missing):
            backend, report = compat.probe_pidfd_support()
        if not report['ready']:
            self.skipTest('Runtime does not expose this pidfd path: ' + json.dumps(report['probe'], sort_keys=True))
        return backend, report

    def test_real_self_probe_works_with_both_python_attributes_removed(self):
        with mock.patch.object(os, 'kill', side_effect=AssertionError('Numeric PID signaling is forbidden')):
            _, report = self.ready_backend('open', 'send_signal')
        self.assertEqual(report['selected_backend'], {'open': 'libc', 'send_signal': 'libc'})
        self.assertFalse(report['python_api']['os_pidfd_open_present'])
        self.assertFalse(report['python_api']['signal_pidfd_send_signal_present'])
        self.assertEqual(report['probe']['target'], 'CURRENT_PROCESS_ONLY')
        self.assertEqual(report['probe']['signal'], 0)
        self.assertFalse(report['probe']['signal_delivered'])
        self.assertEqual(report['operation_counts']['libc_open'], 1)
        self.assertEqual(report['operation_counts']['libc_send_signal'], 1)

    def test_each_individual_missing_python_operation_uses_its_libc_export(self):
        for missing in ('open', 'send_signal'):
            with self.subTest(missing=missing):
                _, report = self.ready_backend(missing)
                self.assertEqual(report['selected_backend'][missing], 'libc')

    def test_owned_child_signal_zero_harmless_signal_and_stale_handle(self):
        backend, _ = self.ready_backend('open', 'send_signal')
        descriptor = None
        try:
            with cooperative_child() as original, \
                    mock.patch.object(os, 'kill', side_effect=AssertionError('Numeric PID signaling is forbidden')):
                descriptor = backend.open(original.pid, 0)
                self.assertFalse(os.get_inheritable(descriptor))
                backend.send_signal(descriptor, 0, None, 0)
                self.assertIsNone(original.poll())
                self.assertEqual(select.select([descriptor], [], [], 0)[0], [])
                backend.send_signal(descriptor, signal.SIGUSR1, None, 0)
                self.assertTrue(select.select([original.stdout], [], [], 5)[0])
                self.assertEqual(original.stdout.readline().strip(), 'ACK')
                original.stdin.write('EXIT\n')
                original.stdin.flush()
                self.assertEqual(original.wait(timeout=5), 0)
                self.assertTrue(select.select([descriptor], [], [], 1)[0])
            with cooperative_child() as unrelated, \
                    mock.patch.object(os, 'kill', side_effect=AssertionError('Numeric PID signaling is forbidden')):
                for sig in (0, signal.SIGUSR1):
                    with self.assertRaises(OSError) as caught:
                        backend.send_signal(descriptor, sig, None, 0)
                    self.assertEqual(caught.exception.errno, errno.ESRCH)
                self.assertIsNone(unrelated.poll())
                self.assertEqual(select.select([unrelated.stdout], [], [], 0)[0], [])
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def test_real_closed_pidfd_returns_ebadf(self):
        backend, _ = self.ready_backend('open', 'send_signal')
        descriptor = backend.open(os.getpid())
        os.close(descriptor)
        with self.assertRaises(OSError) as caught:
            backend.send_signal(descriptor, 0)
        self.assertEqual(caught.exception.errno, errno.EBADF)


if __name__ == '__main__':
    unittest.main()
