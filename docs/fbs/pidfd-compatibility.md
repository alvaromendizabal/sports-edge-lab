# Linux pidfd compatibility across Python builds

The standard-library-only [pidfd adapter](../../examples/fbs_contracts/pidfd_compat.py) selects each callable Python pidfd function independently and uses an exported libc wrapper when that Python function is absent. Its self-probe opens a handle to the current process, requests signal 0, and closes the handle. The probe delivers no signal.

The accompanying [tests](../../examples/fbs_contracts/tests/test_pidfd_compat.py) exercise the real libc path with Python's attributes removed, verify a harmless signal to an owned child, and verify that its retained handle returns `ESRCH` after cooperative exit and reaping. The tests also cover unavailable functions, exact errno propagation, descriptor cleanup, mixed Python/libc selection, and integer overflow rejection. No machine-learning dependencies, credentials, network access, process discovery, or application-specific files are required.

## Why a Python attribute check is insufficient

Python documents `os.pidfd_open` and `signal.pidfd_send_signal` as Linux interfaces added in Python 3.9. Their kernel requirements differ: opening a pidfd needs Linux 5.3 or later; sending through one needs Linux 5.1 or later. [Python os documentation](https://docs.python.org/3.12/library/os.html#os.pidfd_open), [Python signal documentation](https://docs.python.org/3.12/library/signal.html#signal.pidfd_send_signal).

A runtime can omit a Python wrapper despite having the necessary Linux and libc support. For example, CPython 3.12 compiles its `os.pidfd_open` implementation only when both Linux and the `__NR_pidfd_open` build-time macro are defined. This makes an absent attribute evidence about that Python build; it does not establish the running kernel's capability or current permissions. [CPython 3.12 implementation](https://github.com/python/cpython/blob/3.12/Modules/posixmodule.c).

glibc added exported `pidfd_open`, `pidfd_getfd`, and `pidfd_send_signal` wrappers in version 2.36. The adapter detects exports in the running process rather than accepting a version string as proof that calls will work. [Official glibc 2.36 announcement](https://sourceware.org/pipermail/libc-announce/2022/000034.html).

| Layer | What the adapter checks | What the check establishes |
|---|---|---|
| Python | Each attribute's presence and callability | Whether that Python wrapper can be selected |
| Loaded libc | Each exported function | Whether the fallback wrapper can be selected |
| Kernel and current permissions | Actual self pidfd open and signal-0 calls | Whether these operations worked for the current process at probe time |
| Application policy | The caller's separate process and ownership checks | Whether a particular target and action are authorized |

## ABI and error handling

The libc functions have these C interfaces:

```c
int pidfd_open(pid_t pid, unsigned int flags);
int pidfd_send_signal(int pidfd, int sig, siginfo_t *info,
                      unsigned int flags);
```

The bindings use `ctypes.c_int` for the return value, PID, descriptor and signal; `ctypes.c_uint` for flags; and `ctypes.c_void_p` for the nullable information pointer. Linux's PID type uses a signed 32-bit integer in the supported ABI. The adapter checks integers before conversion because ctypes integer conversion does not itself provide overflow checking. It accepts only flags 0 and a null information pointer, so it does not expose newer group-scoping flags or construct a platform-dependent `siginfo_t`. The official glibc changes show the exported signatures and the `GLIBC_2.36` ABI entries: [open implementation](https://sourceware.org/pipermail/glibc-cvs/2022q2/079051.html), [send implementation](https://sourceware.org/pipermail/glibc-cvs/2022q2/079053.html). Python documents the C-type mappings and conversion behavior in its [ctypes reference](https://docs.python.org/3.12/library/ctypes.html).

The fallback loads the current process's symbols using `ctypes.CDLL(None, use_errno=True)`. It declares `argtypes` and `restype` before use, clears ctypes' saved errno before each call, and converts a return value of -1 into `OSError` carrying the immediately captured errno. `use_errno=True` preserves errno through ctypes' thread-local mechanism. If a foreign function unexpectedly fails without setting errno, the adapter reports `EIO` instead of reusing a stale error. [ctypes errno documentation](https://docs.python.org/3.12/library/ctypes.html#ctypes.get_errno).

Backend selection is fixed for each adapter instance. An operational failure does not cause a retry through another backend. The caller receives errors such as `ENOSYS`, `EPERM`, `ESRCH`, `EBADF`, `EINVAL`, or descriptor/memory resource errors. A version string does not override those results. The adapter contains no architecture-specific syscall numbers and no numeric-PID signal fallback. [Linux open errors](https://man7.org/linux/man-pages/man2/pidfd_open.2.html), [Linux send errors](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html).

Some Linux man-pages currently retain a note saying that glibc supplies no wrappers for these operations. That note conflicts with glibc's 2.36 release announcement and exported ABI changes linked above. The adapter uses detected exports and actual calls; it does not depend on that note.

## Running the compatibility probe and tests

From the repository root on Linux with Python 3.11 or later:

```bash
python - <<'PY'
import json
from examples.fbs_contracts.pidfd_compat import probe_pidfd_support

backend, report = probe_pidfd_support()
print(json.dumps(report, indent=2, sort_keys=True))
if not report["ready"]:
    raise SystemExit("PID-handle capability probe did not pass")
PY

python -m unittest discover -s examples/fbs_contracts/tests -p test_pidfd_compat.py -v
```

The JSON report distinguishes missing Python attributes, missing libc exports, selected backends, actual call counts, and the operation/errno of a failed probe. Real-runtime tests explicitly skip when their required kernel or libc path is unavailable; deterministic refusal tests still run. Review skipped tests when assessing a particular deployment. Passing tests on one host does not certify another host's kernel, libraries, security policy, or target permissions.

## Process identity remains the caller's responsibility

A pidfd remains bound to the process it references. Once that process exits and is reaped, signaling through its retained handle fails with `ESRCH`; it does not select a new process by a recycled numeric PID. The real-child test checks this stale-handle behavior and confirms that an unrelated child remains alive. It does not claim to force the kernel to recycle a numeric PID. [Linux pidfd identity semantics](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html).

Opening a handle still begins with a numeric PID. A caller managing an existing process must independently verify the intended process identity, ownership, executable and relevant lock or task evidence, then recheck identity around handle acquisition before any consequential signal. A successful self-probe is not approval to act on another process and does not prove permission to do so. Keep the pidfd open until the operation completes; close it exactly once afterward.

The adapter supplies capability detection and the narrow operating-system interface. It does not select an application run, freeze a writer, terminate work, remove a lock, or recover a database. Those decisions require separate, application-specific evidence and authorization.
