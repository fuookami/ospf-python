"""RG-029 的可执行回归：SCIP 带 `on_progress` 的求解每次泄漏约 2.5 MiB。

背景：`docs/migration/rust-gaps.md` 的 RG-029 记录了这条上游缺口——
`ospf-rust` 的 scip 插件（`russcip 0.9.1`）在 `telemetry_callback` 非空时，
每次求解泄漏约 2.5 MiB，与模型规模无关。三条路径已实测：
`model.solve` 2.5 MiB/次、`bpp1d.solve` 2.5 MiB/次、`gantt_task.solve_lp` 5.24 MiB/轮。

**RG-029 已在 `ospf-rust` 修复（提交 `b9ab844`：`Variable` 不再持有 `ScipPtr` 的强引用，
打破引用环）。本文件此前用 `xfail(strict=True)` 把缺口钉住；修复生效后该标记
按 strict 规矩移除，用例现在直接断言不泄漏。**

**RG-029 has been fixed upstream (commit `b9ab844`); the strict xfail was removed
per the usual rule once the test started passing.**
- 修好之后 → **xpass → 套件变红**，迫使删除这个标记并留下真正的通过断言。

这样缺口既不会「只在 logs 里」，也不会让套件长期红。

只在编译了 scip 后端的构建上运行；其它构建 skip。
"""

from __future__ import annotations

import ctypes
import gc
import sys
import time
from ctypes import wintypes

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="Windows process counters"
)

ROUNDS = 8
# 缺口存在时 8 轮 × ~2.5 MiB ≈ 20 MiB；上限设 4 MiB 与既有生命周期用例一致。
GROWTH_LIMIT = 4 * 1024**2


class _ProcessMemoryCounters(ctypes.Structure):
    """PROCESS_MEMORY_COUNTERS。"""

    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


def _private_usage() -> int:
    """当前进程 PrivateUsage。"""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_ProcessMemoryCounters),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return counters.PrivateUsage


def _scip_compiled() -> bool:
    """当前扩展是否编译了 scip 后端。"""
    from ospf_python import _native  # noqa: PLC0415

    return "scip" in _native.build_info()["native_solvers"].split(",")


@pytest.mark.skipif(
    not _scip_compiled(), reason="Rust backend not compiled: scip"
)
def test_scip_progress_callback_does_not_leak_per_solve() -> None:
    """8 次带回调的求解，内存增长不得超过 4 MiB（RG-029）。"""
    from tests.native.test_model_lifecycle_stress import _solve_once  # noqa: PLC0415

    _solve_once("scip")  # 预热：让一次性池先建立
    gc.collect()
    time.sleep(0.1)
    start = _private_usage()
    for _ in range(ROUNDS):
        _solve_once("scip")
    gc.collect()
    time.sleep(0.2)
    growth = _private_usage() - start
    assert growth <= GROWTH_LIMIT, (
        f"RG-029 复现：{ROUNDS} 次带回调的 scip 求解增长 {growth:,} B"
        f"（上限 {GROWTH_LIMIT:,}），每轮约 {growth // ROUNDS:,} B"
    )


@pytest.mark.skipif(
    not _scip_compiled(), reason="Rust backend not compiled: scip"
)
def test_scip_without_progress_callback_does_not_leak() -> None:
    """对照：**不传** `on_progress` 时不泄漏——证明差异来自回调而非生命周期。"""
    from ospf_python._binding.model import MetaModelFloat64, VariableSpec  # noqa: PLC0415
    from tests.native.test_model_lifecycle_stress import _SolverCallback  # noqa: PLC0415

    def solve_once() -> None:
        model = MetaModelFloat64.create("no-callback").unwrap()
        try:
            variable = model.add_variables(
                [VariableSpec(name="x", lower=0, upper=1)]
            ).unwrap()[0]
            model.set_objective(terms=[(variable, 1)], sense="maximize").unwrap()
            model.solve(solver="scip").unwrap()
        finally:
            model.close().unwrap()

    assert _SolverCallback is not None
    solve_once()  # 预热
    gc.collect()
    time.sleep(0.1)
    start = _private_usage()
    for _ in range(ROUNDS):
        solve_once()
    gc.collect()
    time.sleep(0.2)
    growth = _private_usage() - start
    assert growth <= GROWTH_LIMIT, (
        f"不带回调也不应泄漏：{ROUNDS} 次求解增长 {growth:,} B"
        f"（上限 {GROWTH_LIMIT:,}）"
    )
