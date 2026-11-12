"""模型生命周期循环压力合同 / Model lifecycle loop-stress contracts."""

from __future__ import annotations

import ctypes
import gc
import sys
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from ctypes import wintypes
from typing import TYPE_CHECKING

import pytest

from ospf_python import _native
from ospf_python._binding.model import MetaModelFloat64, VariableSpec
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

if TYPE_CHECKING:
    from ospf_python._binding.control import SolveProgress

GROWTH_LIMIT = 4 * 1024**2
# 线程回落截止时间：5 s 在空载下足够（实测 0.12–0.19 s），但全量套件里 GC 压力会拖慢回收。
# Thread-settle deadline: 5 s suffices idle, but full-suite GC pressure slows reclamation.
SETTLE_DEADLINE_S = 15.0
PEAK_LIMIT = 24 * 1024**2
WARMUP_MODELS = 16
BATCH_MODELS = 64
BATCHES = 4
VARIABLES_PER_MODEL = 20
SOLVER_MODELS_PER_BATCH = 8
SOLVER_BATCHES = 4
PARALLEL_MODELS = 32
PARALLEL_WORKERS = 8


class _SolverCallback:
    def __init__(self) -> None:
        self.events: list[SolveProgress] = []

    def __call__(self, event: SolveProgress) -> None:
        self.events.append(event)


class _MemoryCounters(ctypes.Structure):
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


class _ThreadEntry(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ThreadID", wintypes.DWORD),
        ("th32OwnerProcessID", wintypes.DWORD),
        ("tpBasePri", wintypes.LONG),
        ("tpDeltaPri", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
    ]


def _memory() -> dict[str, int]:
    gc.collect()
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_MemoryCounters),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    counters = _MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return {
        name: getattr(counters, name)
        for name in ("WorkingSetSize", "PeakWorkingSetSize", "PrivateUsage")
    }


def _thread_count() -> int:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Thread32First.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_ThreadEntry),
    ]
    kernel32.Thread32First.restype = wintypes.BOOL
    kernel32.Thread32Next.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_ThreadEntry),
    ]
    kernel32.Thread32Next.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.GetCurrentProcessId.restype = wintypes.DWORD
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000004, 0)
    invalid = ctypes.c_void_p(-1).value
    if snapshot == invalid or snapshot is None:
        raise ctypes.WinError(ctypes.get_last_error())
    process = kernel32.GetCurrentProcessId()
    entry = _ThreadEntry()
    entry.dwSize = ctypes.sizeof(entry)
    count = 0
    try:
        present = kernel32.Thread32First(snapshot, ctypes.byref(entry))
        while present:
            if entry.th32OwnerProcessID == process:
                count += 1
            present = kernel32.Thread32Next(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return count


def _settle_threads(*, baseline: int, deadline_s: float = SETTLE_DEADLINE_S) -> int:
    """等线程回落到基线，返回最终计数。

    截止时间从 5 s 放宽到 15 s：断言的**不变量**仍是「线程数回到基线」，
    放宽的只是「等多久」。**这不掩盖泄漏**——真泄漏时线程永远不会回落，
    再长的截止时间也会失败；它只容忍全量套件上下文里的缓慢回收。

    Patience, not the invariant: the assertion still requires the count to return to baseline.
    A real leak never returns regardless of the deadline, so this only tolerates slow
    reclamation under a full-suite load.
    """
    deadline = time.monotonic() + deadline_s
    current = _thread_count()
    while current > baseline and time.monotonic() < deadline:
        gc.collect()
        time.sleep(0.02)
        current = _thread_count()
    return current


def _thousands_plateau(*, deadline_s: float = 2.0) -> int:
    """等线程数**稳定下来**（连续两次相同即认为到稳态），返回那个数。

    与 `_settle_threads` 的区别：这里没有目标基线，只等计数停止变化——
    用于「预热之后取基线」。 / Wait for the count to stop changing, with no target.
    """
    deadline = time.monotonic() + deadline_s
    previous = _thread_count()
    while time.monotonic() < deadline:
        gc.collect()
        time.sleep(0.05)
        current = _thread_count()
        if current == previous:
            return current
        previous = current
    return previous


def _exercise(
    *, count: int, explicit_close: bool
) -> list[weakref.ReferenceType[MetaModelFloat64]]:
    references = []
    for index in range(count):
        model = MetaModelFloat64.create(f"stress-{index}").unwrap()
        references.append(weakref.ref(model))
        variables = model.add_variables(
            [
                VariableSpec(name=f"x-{position}", lower=0, upper=1)
                for position in range(VARIABLES_PER_MODEL)
            ]
        ).unwrap()
        assert len(variables) == VARIABLES_PER_MODEL
        assert model.snapshot().unwrap()[2] == VARIABLES_PER_MODEL
        if explicit_close:
            assert model.close().is_ok()
        del variables, model
    gc.collect()
    return references


def _solve_once(solver: str) -> weakref.ReferenceType[_SolverCallback]:
    model = MetaModelFloat64.create("solver-stress").unwrap()
    callback = _SolverCallback()
    reference = weakref.ref(callback)
    try:
        variable = model.add_variables(
            [VariableSpec(name="x", lower=0, upper=1)]
        ).unwrap()[0]
        model.set_objective(terms=[(variable, 1)], sense="maximize").unwrap()
        report = model.solve(solver=solver, on_progress=callback).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((1,))
        assert report.objective == pytest.approx(1)
        assert callback.events
        assert callback.events[-1].terminal
    finally:
        model.close().unwrap()
    return reference


def _solve_batch(
    solver: str, count: int
) -> list[weakref.ReferenceType[_SolverCallback]]:
    references = [_solve_once(solver) for _ in range(count)]
    gc.collect()
    assert all(reference() is None for reference in references)
    return references


def _parallel_owner(index: int) -> None:
    model = MetaModelFloat64.create(f"parallel-stress-{index}").unwrap()
    try:
        variables = model.add_variables(
            [
                VariableSpec(name=f"x-{position}", lower=0, upper=1)
                for position in range(VARIABLES_PER_MODEL)
            ]
        ).unwrap()
        assert len(variables) == VARIABLES_PER_MODEL
        assert model.snapshot().unwrap()[2] == VARIABLES_PER_MODEL
    finally:
        model.close().unwrap()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process counters")
def test_repeated_model_lifecycle_reclaims_threads_and_memory() -> None:
    # 基线必须在**预热之后**取：solver 后端（Gurobi/SCIP）会建常驻线程池，
    # 预热前取基线会让「第一批」永远超标——那不是泄漏，是后端的一次性初始化。
    # 预热后进入稳态，这个基线才是「本测试应当回落到」的值。
    # The baseline must be taken AFTER the warm-up: solver backends keep persistent thread
    # pools, so a pre-warm-up baseline makes the first batch always exceed it. That is
    # one-time backend initialisation, not a leak. Post-warm-up is the steady state.
    before = _memory()
    references = _exercise(count=WARMUP_MODELS, explicit_close=True)
    baseline = _thousands_plateau()
    assert all(reference() is None for reference in references)
    warm = _memory()
    samples = []
    for batch in range(BATCHES):
        references = _exercise(
            count=BATCH_MODELS,
            explicit_close=batch % 2 == 0,
        )
        settled = _settle_threads(baseline=baseline)
        assert settled <= baseline, (
            f"第 {batch} 批后线程未回落：基线 {baseline}，当前 {settled}"
        )
        assert all(reference() is None for reference in references)
        samples.append(_memory())
    growth = max(
        0,
        max(sample["PrivateUsage"] - warm["PrivateUsage"] for sample in samples),
    )
    peak_increment = max(
        0,
        max(sample["PeakWorkingSetSize"] for sample in samples)
        - before["WorkingSetSize"],
    )
    assert growth <= GROWTH_LIMIT
    assert peak_increment <= PEAK_LIMIT


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process counters")
def test_repeated_model_lifecycle_preserves_identity_and_closed_contracts() -> None:
    identities: set[int] = set()
    for _ in range(32):
        local = MetaModelFloat64.create("same-name").unwrap()
        foreign = MetaModelFloat64.create("same-name").unwrap()
        try:
            local_identity = local.model_identity
            assert local_identity not in identities
            identities.add(local_identity)
            local_variable = local.add_variables(
                [VariableSpec(name="x", lower=0, upper=2)]
            ).unwrap()[0]
            foreign_variable = foreign.add_variables(
                [VariableSpec(name="x", lower=0, upper=2)]
            ).unwrap()[0]
            assert isinstance(
                local.set_bounds(handle=foreign_variable, lower=0, upper=1),
                Failed,
            )
            assert isinstance(
                foreign.set_bounds(handle=local_variable, lower=0, upper=1),
                Failed,
            )
            assert local.close().is_ok()
            assert local.close().is_ok()
            assert local.model_identity == local_identity
            for result in (
                local.snapshot(),
                local.add_variables([VariableSpec(name="closed")]),
                local.set_bounds(handle=local_variable, lower=0, upper=1),
            ):
                assert isinstance(result, Failed)
                assert result.error.code is ErrorCode.NOT_INITIALIZED
        finally:
            local.close().unwrap()
            foreign.close().unwrap()
    gc.collect()


@pytest.fixture(
    params=[
        # RG-029 已在 ospf-rust 修复（`b9ab844`：`Variable` 不再持有 `ScipPtr` 强引用，
        # 打破引用环使 `SCIPfree` 得以调用）。此前 scip 这一项挂着 strict xfail
        # （4 批 × 4 模型 ≈ 40 MiB 泄漏，超过 4 MiB 上限）；修复生效后按规矩移除标记。
        # RG-029 is fixed upstream (commit `b9ab844`); the strict xfail was removed.
        "scip",
        "gurobi10",
        "gurobi11",
        "gurobi12",
    ]
)
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process counters")
def test_repeated_solver_sessions_reclaim_threads_memory_and_callbacks(
    solver: str,
) -> None:
    # 与 `test_repeated_model_lifecycle_reclaims_threads_and_memory` 同理：
    # 基线必须在预热求解之后取——solver 后端会建常驻线程池（SCIP 尤其明显），
    # 预热前的基线会让第一批永远超标，那不是泄漏。
    # Same reasoning as the model-lifecycle test: take the baseline AFTER the warm-up solve,
    # because solver backends keep persistent thread pools (SCIP especially).
    before = _memory()
    _solve_batch(solver, 4)
    baseline = _thousands_plateau()
    warm = _memory()

    samples = []
    for _ in range(SOLVER_BATCHES):
        _solve_batch(solver, SOLVER_MODELS_PER_BATCH)
        assert _settle_threads(baseline=baseline) <= baseline
        samples.append(_memory())

    growth = max(
        0,
        max(sample["PrivateUsage"] - warm["PrivateUsage"] for sample in samples),
    )
    peak_increment = max(
        0,
        max(sample["PeakWorkingSetSize"] for sample in samples)
        - before["WorkingSetSize"],
    )
    assert growth <= GROWTH_LIMIT
    assert peak_increment <= PEAK_LIMIT


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process counters")
def test_parallel_model_owners_reclaim_threads_and_memory() -> None:
    before = _memory()
    baseline = _thread_count()
    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        list(pool.map(_parallel_owner, range(PARALLEL_MODELS)))

    assert _settle_threads(baseline=baseline) <= baseline
    after = _memory()
    assert after["PrivateUsage"] - before["PrivateUsage"] <= GROWTH_LIMIT
    assert after["PeakWorkingSetSize"] - before["WorkingSetSize"] <= PEAK_LIMIT
