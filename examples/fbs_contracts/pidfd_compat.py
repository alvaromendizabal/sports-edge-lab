"""PID-handle operations across Python builds, without numeric-PID signaling.

Python may omit a wrapper even when Linux and glibc provide the operation.
Select each callable Python wrapper first, otherwise use the exported libc
wrapper with its declared ABI. An operational failure never changes backends.
No raw syscall numbers, permission workarounds, or os.kill fallback are used.
"""
from __future__ import annotations

import copy
import ctypes
import errno
import operator
import os
import platform
import signal
import sys


class PidfdUnavailable(RuntimeError):
    """Neither supported wrapper exposes a required PID-handle operation."""


def _load_libc():
    return ctypes.CDLL(None, use_errno=True)


def _signed_int(value, name, *, minimum=0):
    if isinstance(value, bool):
        raise TypeError(name + ' must be an integer, not a boolean')
    result = operator.index(value)
    if result < minimum or result > 2 ** 31 - 1:
        raise ValueError(name + ' is outside the supported signed-int range')
    return result


def _error(exc, operation):
    number = getattr(exc, 'errno', None)
    return {'operation': operation, 'exception': type(exc).__name__,
            'errno': number, 'errno_name': errno.errorcode.get(number), 'message': str(exc)}


class PidfdBackend:
    """Stable per-operation selection of callable Python or exported libc APIs."""

    def __init__(self):
        self._python_open = getattr(os, 'pidfd_open', None)
        self._python_send = getattr(signal, 'pidfd_send_signal', None)
        self._libc = None
        self._native_open = self._native_send = None
        self._calls = {'python_open': 0, 'python_send_signal': 0,
                       'libc_open': 0, 'libc_send_signal': 0}
        self._diagnostics = {
            'schema': 'fbs.v004.pidfd-capability',
            'platform': {'sys_platform': sys.platform, 'kernel': platform.release(),
                         'machine': platform.machine(), 'python': platform.python_version(),
                         'python_implementation': platform.python_implementation(),
                         'libc': list(platform.libc_ver())},
            'python_api': {
                'os_pidfd_open_present': hasattr(os, 'pidfd_open'),
                'os_pidfd_open_callable': callable(self._python_open),
                'signal_pidfd_send_signal_present': hasattr(signal, 'pidfd_send_signal'),
                'signal_pidfd_send_signal_callable': callable(self._python_send)},
            'libc_api': {'loaded': False, 'pidfd_open_exported': False,
                         'pidfd_send_signal_exported': False, 'errors': []},
            'selected_backend': {'open': None, 'send_signal': None},
            'numeric_pid_signal_fallback': False, 'direct_syscalls_used': False,
        }
        if sys.platform != 'linux':
            self._diagnostics['libc_api']['errors'].append({
                'operation': 'platform', 'exception': 'UnsupportedPlatform',
                'errno': None, 'errno_name': None, 'message': 'Linux PID handles are required'})
            return
        try:
            self._libc = _load_libc()
            self._diagnostics['libc_api']['loaded'] = True
        except (OSError, AttributeError) as exc:
            self._diagnostics['libc_api']['errors'].append(_error(exc, 'load_libc'))
        if self._libc is not None:
            for symbol, arguments, attribute in (
                    ('pidfd_open', [ctypes.c_int, ctypes.c_uint], '_native_open'),
                    ('pidfd_send_signal', [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint], '_native_send')):
                function = getattr(self._libc, symbol, None)
                if callable(function):
                    function.argtypes, function.restype = arguments, ctypes.c_int
                    setattr(self, attribute, function)
                    self._diagnostics['libc_api'][symbol + '_exported'] = True
        selected = self._diagnostics['selected_backend']
        selected['open'] = 'python' if callable(self._python_open) else 'libc' if self._native_open is not None else None
        selected['send_signal'] = 'python' if callable(self._python_send) else 'libc' if self._native_send is not None else None

    @property
    def available(self):
        return all(self._diagnostics['selected_backend'].values())

    def diagnostics(self):
        return {**copy.deepcopy(self._diagnostics), 'available': self.available,
                'operation_counts': dict(self._calls)}

    @staticmethod
    def _native_call(function, *arguments):
        ctypes.set_errno(0)
        result = function(*arguments)
        if result == -1:
            number = ctypes.get_errno()
            if not number:
                number = errno.EIO
            raise OSError(number, os.strerror(number))
        return result

    def open(self, pid, flags=0):
        pid = _signed_int(pid, 'pid', minimum=1)
        if flags != 0:
            raise ValueError('Only flags=0 is supported for recovery PID handles')
        selected = self._diagnostics['selected_backend']['open']
        if selected == 'python':
            self._calls['python_open'] += 1
            return self._python_open(pid, 0)
        if selected == 'libc':
            self._calls['libc_open'] += 1
            return self._native_call(self._native_open, pid, 0)
        raise PidfdUnavailable('Neither a callable Python pidfd_open nor an exported libc pidfd_open is available')

    def send_signal(self, pidfd, sig, siginfo=None, flags=0):
        pidfd = _signed_int(pidfd, 'pidfd')
        sig = _signed_int(sig, 'signal')
        if sig >= signal.NSIG:
            raise ValueError('Signal number is outside this platform signal range')
        if siginfo is not None or flags != 0:
            raise ValueError('Only siginfo=None and flags=0 are supported for recovery signals')
        selected = self._diagnostics['selected_backend']['send_signal']
        if selected == 'python':
            self._calls['python_send_signal'] += 1
            return self._python_send(pidfd, sig, None, 0)
        if selected == 'libc':
            self._calls['libc_send_signal'] += 1
            return self._native_call(self._native_send, pidfd, sig, None, 0)
        raise PidfdUnavailable('Neither a callable Python pidfd_send_signal nor an exported libc pidfd_send_signal is available')


def probe_pidfd_support():
    """Return (selected backend, report) after signal 0 against our own pidfd.

    Signal 0 checks existence and permission without delivering a signal. Any
    error is reported exactly and the caller must refuse target signaling.
    """
    backend = PidfdBackend()
    report = backend.diagnostics()
    report.update({'probe': {'target': 'CURRENT_PROCESS_ONLY', 'signal': 0,
                             'signal_delivered': False, 'status': 'NOT_STARTED'},
                   'ready': False})
    descriptor, operation = None, 'open_self_pidfd'
    try:
        if not backend.available:
            raise PidfdUnavailable('Required PID-handle wrapper selection is incomplete')
        descriptor = backend.open(os.getpid(), 0)
        operation = 'signal_zero_self_pidfd'
        backend.send_signal(descriptor, 0, None, 0)
        report['probe']['status'] = 'PASSED'
        report['ready'] = True
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        report['probe']['status'] = 'FAILED'
        report['probe']['error'] = _error(exc, operation)
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError as exc:
                report['ready'] = False
                report['probe']['status'] = 'FAILED'
                report['probe']['close_error'] = _error(exc, 'close_self_pidfd')
        report['operation_counts'] = backend.diagnostics()['operation_counts']
    return backend, report
