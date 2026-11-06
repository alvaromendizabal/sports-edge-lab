"""Pure, invented storage-admission examples for the public NBA track.

Inputs are supplied records. This example performs no filesystem mutation,
network operation, data acquisition, model execution or cleanup.
"""
from dataclasses import dataclass


def _bytes(value):
    if type(value) is not int or value < 0:
        raise ValueError("Byte quantities must be nonnegative integers")
    return value


@dataclass(frozen=True)
class Volume:
    label: str
    device: str
    free_bytes: int
    writable: bool = True
    memory_backed: bool = False

    def __post_init__(self):
        _bytes(self.free_bytes)
        if not self.label or not self.device:
            raise ValueError("A volume needs an explicit label and device identity")


@dataclass(frozen=True)
class WorkspaceBinding:
    project: str
    build: str
    workspace: str
    device: str
    principal: str

    def __post_init__(self):
        if self.project != "nba" or not all((self.build, self.workspace, self.device, self.principal)):
            raise ValueError("An explicit NBA workspace identity is required")


def choose_volume(home, candidates, *, phase_peaks, return_reserve, work_reserve):
    """Account for coexisting phase bytes and shared storage exactly once.

    Each phase peak is the complete projected allocation at that phase, not an
    incremental write count. The largest peak controls initial admission.
    """
    if not phase_peaks or not all(isinstance(name, str) and name for name in phase_peaks):
        raise ValueError("Named phase allocations are required")
    peak = max(_bytes(value) for value in phase_peaks.values())
    _bytes(return_reserve); _bytes(work_reserve)
    observations = []
    for candidate in (home, *candidates):
        shared = candidate.device == home.device
        usable = min(candidate.free_bytes, home.free_bytes) if shared else candidate.free_bytes
        required = peak + work_reserve + (return_reserve if shared else 0)
        reasons = []
        if not candidate.writable:
            reasons.append("READ_ONLY")
        if candidate.memory_backed:
            reasons.append("MEMORY_CAPACITY_IS_NOT_DISK_CAPACITY")
        if not home.writable or home.memory_backed:
            reasons.append("HOME_RETURN_VOLUME_UNAVAILABLE")
        if home.free_bytes < return_reserve:
            reasons.append("RETURN_RESERVE_UNAVAILABLE")
        if usable < required:
            reasons.append("PHASE_CAPACITY_UNAVAILABLE")
        if candidate is not home and shared:
            reasons.append("SHARED_DEVICE_ADDS_NO_CAPACITY")
        observations.append({"label": candidate.label, "same_device_as_home": shared,
                             "usable_bytes": usable, "required_bytes": required, "reasons": reasons})
        if not reasons:
            return {"admitted": True, "selected": candidate.label, "phase_peak_bytes": peak,
                    "observations": observations, "capacity_is_reserved": False}
    return {"admitted": False, "selected": None, "phase_peak_bytes": peak,
            "observations": observations, "capacity_is_reserved": False}


def validate_resume(expected, observed, *, exists, is_symlink, private_permissions):
    """A missing or changed workspace must not silently start a new run."""
    if not exists:
        raise ValueError("Authenticated recovery is required for a missing workspace")
    if is_symlink or not private_permissions:
        raise ValueError("The workspace must retain its private filesystem identity")
    if expected != observed:
        raise ValueError("The recorded workspace binding changed")
    return {"binding_valid": True, "silent_fallback_permitted": False}


def admit_next_write(free_bytes, *, next_file_bytes, unfilled_sparse_bytes, reserve_bytes):
    """Sparse truncate alone does not reserve the storage needed to fill files."""
    return _bytes(free_bytes) >= (_bytes(next_file_bytes) + _bytes(unfilled_sparse_bytes)
                                 + _bytes(reserve_bytes))
