"""形状计算的低内存边界 / Low-memory boundaries for shape arithmetic."""

from __future__ import annotations

import ctypes
import subprocess
import sys
from ctypes import wintypes

import pytest


def _run_with_memory_pressure(
    *, child_source: str, case: str, headroom: int | None = None
) -> None:
    class BasicLimits(ctypes.Structure):
        _fields_ = [
            ("process_time", ctypes.c_longlong),
            ("job_time", ctypes.c_longlong),
            ("flags", wintypes.DWORD),
            ("minimum_working_set", ctypes.c_size_t),
            ("maximum_working_set", ctypes.c_size_t),
            ("active_processes", wintypes.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority", wintypes.DWORD),
            ("scheduling", wintypes.DWORD),
        ]

    class IoCounters(ctypes.Structure):
        _fields_ = [(f"counter_{i}", ctypes.c_ulonglong) for i in range(6)]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("basic", BasicLimits),
            ("io", IoCounters),
            ("process_memory", ctypes.c_size_t),
            ("job_memory", ctypes.c_size_t),
            ("peak_process_memory", ctypes.c_size_t),
            ("peak_job_memory", ctypes.c_size_t),
        ]

    class ProcessCounters(ctypes.Structure):
        _fields_ = [
            ("size", wintypes.DWORD),
            ("page_faults", wintypes.DWORD),
            *[(f"counter_{i}", ctypes.c_size_t) for i in range(9)],
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    proc = subprocess.Popen(
        [sys.executable, "-u", "-c", child_source, case],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    job = None
    child = None
    try:
        assert proc.stdout is not None
        child_pid = int(proc.stdout.readline())
        child = kernel.OpenProcess(0x0511, False, child_pid)
        if not child:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.basic.flags = 0x100
        limits.process_memory = 6 * 1024 * 1024
        if headroom is not None:
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(ProcessCounters),
                wintypes.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            counters = ProcessCounters()
            counters.size = ctypes.sizeof(counters)
            if not psapi.GetProcessMemoryInfo(
                child, ctypes.byref(counters), counters.size
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            limits.process_memory = counters.counter_8 + headroom
        job = kernel.CreateJobObjectW(None, None)
        if not job:
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.SetInformationJobObject(
            job, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.AssignProcessToJobObject(job, child):
            raise ctypes.WinError(ctypes.get_last_error())
        stdout, stderr = proc.communicate("go\n", timeout=60)
        assert proc.returncode == 0, (proc.returncode, stdout, stderr)
        assert stdout.strip() == "OK"
    finally:
        if proc.poll() is None:
            if proc.stdin:
                proc.stdin.close()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.terminate()
                proc.wait(timeout=10)
        if child:
            kernel.CloseHandle(child)
        if job:
            kernel.CloseHandle(job)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Object test")
@pytest.mark.parametrize(
    "case",
    ["positive", "zero_first", "zero_last", "negative_middle", "large_last", "oom"],
)
def test_dynamic_size_does_not_abort_under_memory_pressure(case: str) -> None:
    """低内存时 size 不终止解释器 / Size must not abort under memory pressure."""

    child_source = """
import ctypes
import os
import sys
handles = [os.add_dll_directory(path) for path in
           os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path]
from ospf_python.multiarray.shape import DynShape
ctypes.windll.kernel32.SetErrorMode(3)
shape = DynShape((1,) * 100_000)
case = sys.argv[1]
if case == 'zero_first':
    vars(shape)['dims'] = (0,) + (1,) * 99_999
elif case == 'zero_last':
    vars(shape)['dims'] = (1,) * 99_999 + (0,)
elif case == 'negative_middle':
    vars(shape)['dims'] = (1,) * 50_000 + (-1,) + (1,) * 49_999
elif case == 'large_last':
    vars(shape)['dims'] = (1,) * 99_999 + (1 << 80,)
elif case == 'oom':
    vars(shape)['dims'] = (1 << 80_000_000, 2)
print(os.getpid(), flush=True)
assert sys.stdin.readline() == 'go\\n'
try:
    value = shape.size
except MemoryError:
    assert case == 'oom'
else:
    expected = {'positive': 1, 'zero_first': 0, 'zero_last': 0,
                'negative_middle': -1, 'large_last': 1 << 80}
    assert case != 'oom' and value == expected[case]
try:
    bytearray(64 * 1024 * 1024)
except MemoryError:
    print('OK', flush=True)
else:
    raise AssertionError('the memory limit did not take effect')
"""
    _run_with_memory_pressure(child_source=child_source, case=case)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Object test")
@pytest.mark.parametrize("order", ["ROW_MAJOR", "COLUMN_MAJOR"])
def test_dense_strides_report_allocation_failure(order: str) -> None:
    """大步长结果分配失败可恢复 / Large stride allocation failure is recoverable."""
    child_source = """
import ctypes
import os
import sys
handles = [os.add_dll_directory(path) for path in
           os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path]
from ospf_python.multiarray.shape import DynShape, StorageOrder
ctypes.windll.kernel32.SetErrorMode(3)
shape = DynShape((1,) * 3_000_000, getattr(StorageOrder, sys.argv[1]))
print(os.getpid(), flush=True)
assert sys.stdin.readline() == 'go\\n'
try:
    shape.strides()
except MemoryError:
    pass
else:
    raise AssertionError('the stride tuple unexpectedly fit within the memory limit')
try:
    bytearray(64 * 1024 * 1024)
except MemoryError:
    print('OK', flush=True)
else:
    raise AssertionError('the memory limit did not take effect')
"""
    _run_with_memory_pressure(child_source=child_source, case=order)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Object test")
@pytest.mark.parametrize("order", ["ROW_MAJOR", "COLUMN_MAJOR"])
def test_dense_strides_report_element_allocation_failure(order: str) -> None:
    """逐项分配失败可恢复 / Element allocation failure is recoverable."""
    child_source = """
import ctypes
import os
import sys
handles = [os.add_dll_directory(path) for path in
           os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path]
from ospf_python.multiarray.shape import DynShape, StorageOrder
ctypes.windll.kernel32.SetErrorMode(3)
rank = 1_000_000
order = getattr(StorageOrder, sys.argv[1])
dims = ((1,) * (rank - 1) + (1 << 50,) if order is StorageOrder.ROW_MAJOR
        else (1 << 50,) + (1,) * (rank - 1))
shape = DynShape(dims, order)
print(os.getpid(), flush=True)
assert sys.stdin.readline() == 'go\\n'
probe = (None,) * rank
assert len(probe) == rank
del probe
try:
    shape.strides()
except MemoryError:
    pass
else:
    raise AssertionError('all large integer strides unexpectedly fit')
try:
    bytearray(64 * 1024 * 1024)
except MemoryError:
    print('OK', flush=True)
else:
    raise AssertionError('the memory limit did not take effect')
"""
    _run_with_memory_pressure(
        child_source=child_source, case=order, headroom=12 * 1024 * 1024
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Object test")
@pytest.mark.parametrize("order", ["ROW_MAJOR", "COLUMN_MAJOR"])
@pytest.mark.parametrize("mode", ["direct", "public"])
def test_dense_flat_index_does_not_abort_under_memory_pressure(
    *, order: str, mode: str
) -> None:
    """稠密索引低内存可恢复 / Dense indexing remains recoverable under pressure."""
    child_source = """
import ctypes
import os
import sys
handles = [os.add_dll_directory(path) for path in
           os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path]
from ospf_python.multiarray.shape import DynShape, StorageOrder, _compute_flat_index
ctypes.windll.kernel32.SetErrorMode(3)
mode, order = sys.argv[1].split(':')
rank = 100_000 if mode == 'direct' else 1_000_000
shape = DynShape((2,) + (1,) * (rank - 1), getattr(StorageOrder, order))
indices = (0,) * rank
strides = shape.strides() if mode == 'direct' else None
print(os.getpid(), flush=True)
assert sys.stdin.readline() == 'go\\n'
try:
    value = (_compute_flat_index(shape.dims, strides, indices) if mode == 'direct'
             else shape.flat_index(*indices))
except MemoryError:
    pass
else:
    assert value == 0
try:
    bytearray(64 * 1024 * 1024)
except MemoryError:
    print('OK', flush=True)
else:
    raise AssertionError('the memory limit did not take effect')
"""
    _run_with_memory_pressure(
        child_source=child_source,
        case=f"{mode}:{order}",
        headroom=28 * 1024 * 1024 if mode == "public" else None,
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Object test")
@pytest.mark.parametrize(
    "case",
    [
        "negative",
        "overbound",
        "short",
        "extra",
        "nonstandard",
        "sparse",
        "wide",
        "huge_stride",
        "negative_huge_stride",
        "huge_index",
        "huge_zero",
        "wide_product",
        "wide_sum",
        "cancellation",
        "late_huge",
        "very_wide",
    ],
)
def test_permissive_flat_index_does_not_abort_under_memory_pressure(case: str) -> None:
    """高维宽松点积可恢复 / High-rank permissive dot products remain recoverable."""
    child_source = """
import ctypes
import os
import sys
handles = [os.add_dll_directory(path) for path in
           os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path]
from ospf_python.multiarray.shape import _compute_flat_index
ctypes.windll.kernel32.SetErrorMode(3)
case = sys.argv[1]
rank = 100_000
dims = (1,) * rank
strides = (1,) * rank
indices = (0,) * rank
expected = 0
if case == 'negative':
    indices = (-1,) + (0,) * (rank - 1)
    expected = -1
elif case == 'overbound':
    indices = (2,) + (0,) * (rank - 1)
    expected = 2
elif case == 'short':
    indices = (1,) * (rank - 1)
    expected = rank - 1
elif case == 'extra':
    indices = indices + (1 << 200,)
elif case == 'nonstandard':
    strides = (2,) + (1,) * (rank - 1)
    indices = (1,) + (0,) * (rank - 1)
    expected = 2
elif case == 'sparse':
    dims = (0,) + (1,) * (rank - 1)
elif case == 'wide':
    strides = (1 << 80,) + (1,) * (rank - 1)
    indices = (1,) + (0,) * (rank - 1)
    expected = 1 << 80
elif case in ('huge_stride', 'negative_huge_stride', 'huge_zero', 'very_wide'):
    wide = 1 << (4096 if case == 'very_wide' else 200)
    wide = -wide if case == 'negative_huge_stride' else wide
    strides = (wide,) + (1,) * (rank - 1)
    indices = (0 if case == 'huge_zero' else 1,) + (0,) * (rank - 1)
    expected = 0 if case == 'huge_zero' else wide
elif case == 'huge_index':
    indices = (1 << 200,) + (0,) * (rank - 1)
    expected = 1 << 200
elif case == 'wide_product':
    strides = (1 << 100,) + (1,) * (rank - 1)
    indices = (1 << 100,) + (0,) * (rank - 1)
    expected = 1 << 200
elif case == 'wide_sum':
    strides = (1 << 126, 1 << 126) + (1,) * (rank - 2)
    indices = (1, 1) + (0,) * (rank - 2)
    expected = 1 << 127
elif case == 'cancellation':
    strides = (1 << 126, 1 << 126, -(1 << 126), -(1 << 126)) + (1,) * (rank - 4)
    indices = (1, 1, 1, 1) + (0,) * (rank - 4)
elif case == 'late_huge':
    strides = (1,) * (rank - 1) + (1 << 200,)
    indices = (0,) * (rank - 1) + (1,)
    expected = 1 << 200
print(os.getpid(), flush=True)
assert sys.stdin.readline() == 'go\\n'
value = _compute_flat_index(dims, strides, indices)
assert type(value) is int and value == expected
try:
    bytearray(64 * 1024 * 1024)
except MemoryError:
    print('OK', flush=True)
else:
    raise AssertionError('the memory limit did not take effect')
"""
    _run_with_memory_pressure(child_source=child_source, case=case)
