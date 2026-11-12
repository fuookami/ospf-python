"""Fixed-runner acceptance for public storage transforms.

The runner pre-registers the complete matrix, seeded inputs, ABBA/BAAB
sampling, resource envelopes and long-soak duration. A report is accepted only
when it is produced on the declared runner, against the pre-registered native
extension, with two complete performance rounds and at least ten minutes of
resource soak.

Usage (smoke):
    python benchmarks/storage_transform_fixed_runner.py --output logs/runner-smoke

Usage (fixed runner):
    OSPF_STORAGE_FIXED_RUNNER=ospf-win-cp313-v1 \
    python benchmarks/storage_transform_fixed_runner.py --output logs/runner-r1 \
      --runner-id ospf-win-cp313-v1 --rounds 2 --soak-seconds 600 \
      --expected-extension-sha256 <sha256> --acceptance
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
POLICY_PATH = HERE / "storage_transform_fixed_runner_policy.json"

if os.name == "nt":
    for _directory in filter(
        None, os.environ.get("OSPF_NATIVE_DLL_DIRS", "").split(os.pathsep)
    ):
        os.add_dll_directory(_directory)

sys.path.insert(0, str(HERE))

from legacy_storage_transform import (  # noqa: E402
    LegacyMultiArray,
    LegacyMutableMultiArray,
)

from ospf_python import _native  # noqa: E402
from ospf_python.multiarray import (  # noqa: E402
    DynShape,
    MultiArray,
    MutableMultiArray,
    Shape2,
    StorageOrder,
)
from ospf_python.quantities.quantity.quantity import Quantity  # noqa: E402
from ospf_python.quantities.unit.length import METER  # noqa: E402


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _values(*, domain: str, count: int, seed: int) -> np.ndarray[Any, Any]:
    rng = np.random.default_rng(seed)
    values = rng.integers(0, 17, size=count, dtype=np.int16)
    if domain == "int16":
        return values
    if domain == "float64":
        return values.astype(np.float64) / 8
    materialized = np.empty(count, dtype=object)
    if domain == "object":
        materialized[:] = [int(value) for value in values]
    elif domain == "quantity":
        materialized[:] = [Quantity(Fraction(int(value), 8), METER) for value in values]
    else:
        raise ValueError(f"unknown domain: {domain}")
    return materialized


def _rss_bytes() -> int:
    """当前进程 RSS（字节）；用 ctypes 直接读 psapi，避免引入依赖。

    Current process RSS in bytes, read through psapi to avoid a new dependency.
    """
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
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

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(Counters),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    ):
        return 0
    return int(counters.WorkingSetSize)


def _timed(*, function: Any, repeats: int) -> float:
    start = time.perf_counter_ns()
    for _ in range(repeats):
        value = function()
        del value
    return (time.perf_counter_ns() - start) / repeats


def _check_pair(
    *,
    native: Any,
    legacy: Any,
    method: str,
    target: DynShape,
    count: int,
) -> None:
    new = native()
    reference = legacy()
    if new._data.dtype != reference._data.dtype:
        raise AssertionError("native and legacy dtype differ")
    if new._data.tolist() != reference._data.tolist():
        raise AssertionError("native and legacy values differ")
    if np.shares_memory(new._data, reference._data):
        raise AssertionError("transform result must own independent storage")
    if method == "reshape":
        if new.shape is not target:
            raise AssertionError("reshape did not preserve target shape identity")
    elif new.shape.dims != (count,):
        raise AssertionError("flatten published unexpected dimensions")
    del new, reference


def _measure_round(
    *,
    policy: dict[str, Any],
    round_index: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seed = policy["seed"]
    domain_index = {name: index for index, name in enumerate(policy["domains"])}
    for count in policy["counts"]:
        for domain in policy["domains"]:
            data = _values(
                domain=domain,
                count=count,
                seed=seed + count + domain_index[domain] * 1_000_003,
            )
            for storage, legacy_storage in (
                (MultiArray, LegacyMultiArray),
                (MutableMultiArray, LegacyMutableMultiArray),
            ):
                for order in policy["orders"]:
                    storage_order = StorageOrder[order]
                    source = storage(Shape2(2, count // 2, storage_order), data)
                    old = legacy_storage(Shape2(2, count // 2, storage_order), data)
                    target = DynShape(
                        (count // 2, 2),
                        (
                            StorageOrder.COLUMN_MAJOR
                            if storage_order is StorageOrder.ROW_MAJOR
                            else StorageOrder.ROW_MAJOR
                        ),
                    )
                    for method in policy["methods"]:
                        legacy = (
                            (lambda old=old, target=target: old.reshape(target))
                            if method == "reshape"
                            else (lambda old=old: old.flatten())
                        )
                        native = (
                            (
                                lambda source=source, target=target: source.reshape(
                                    target
                                ).unwrap()
                            )
                            if method == "reshape"
                            else (lambda source=source: source.flatten().unwrap())
                        )
                        _check_pair(
                            native=native,
                            legacy=legacy,
                            method=method,
                            target=target,
                            count=count,
                        )
                        repeats = policy["repeats_by_count"][str(count)]
                        round_ratios: list[float] = []
                        native_samples: list[float] = []
                        legacy_samples: list[float] = []
                        # 每轮的样本数由 `samples_per_round` 决定（默认 4，即原来的一轮 2 样本/侧）。
                        # 判据边距只有 0.8% 时，18 个样本估不出可复现的比值——B433（0 个失败）与
                        # B434（2 个失败）是同一二进制同一配置的两次不同结果。
                        # `samples_per_round` 放大样本数只改测量精度，不改阈值、不改判据形式。
                        # `samples_per_round` widens each round's sample count. It changes only the
                        # measurement precision, not the threshold or the verdict form.
                        samples_per_round = int(policy.get("samples_per_round", 4))
                        # 逐行追踪（仅在 `OSPF_STORAGE_TRACE=1` 时输出）：
                        # 记录每行开始时的存活块数与行结束时 native/legacy 的中位耗时，
                        # 用于定位「哪一行开始变慢」——纯观测，不改判据。
                        # Per-row trace behind `OSPF_STORAGE_TRACE=1`; observation only.
                        # 注：曾在每行前加 `gc.collect()` 试图消除 round 1 的退化——**实测无效**
                        # （B452：仍 1.34–1.37，且 round 0 的 MutableMultiArray 也被抬高到 1.17）。
                        # Note: a per-row `gc.collect()` was tried to remove the round-1 degradation and
                        # measured ineffective (B452), so it is not kept.
                        trace = os.environ.get("OSPF_STORAGE_TRACE") == "1"
                        if trace:
                            print(
                                f"[trace] row count={count} domain={domain} "
                                f"storage={storage.__name__} order={order} method={method} "
                                f"blocks={sys.getallocatedblocks():,} "
                                f"rss={_rss_bytes():,}",
                                flush=True,
                            )
                        for sample_index in range(policy["alternating_rounds"]):
                            block = (
                                (
                                    ("legacy", legacy),
                                    ("native", native),
                                    ("native", native),
                                    ("legacy", legacy),
                                )
                                if sample_index % 2 == 0
                                else (
                                    ("native", native),
                                    ("legacy", legacy),
                                    ("legacy", legacy),
                                    ("native", native),
                                )
                            )
                            sequence = block * max(1, samples_per_round // len(block))
                            round_native: list[float] = []
                            round_legacy: list[float] = []
                            for mode, function in sequence:
                                sample = _timed(function=function, repeats=repeats)
                                if mode == "native":
                                    round_native.append(sample)
                                    native_samples.append(sample)
                                else:
                                    round_legacy.append(sample)
                                    legacy_samples.append(sample)
                            round_ratios.append(
                                statistics.median(round_native)
                                / statistics.median(round_legacy)
                            )
                        ratio = statistics.median(round_ratios)
                        rows.append(
                            {
                                "count": count,
                                "domain": domain,
                                "storage": storage.__name__,
                                "order": order,
                                "method": method,
                                "ratio": ratio,
                                "round_ratios": round_ratios,
                                "native_samples_ns": native_samples,
                                "legacy_samples_ns": legacy_samples,
                                "round": round_index,
                            }
                        )
    return rows


def _memory() -> dict[str, int]:
    gc.collect()
    if os.name != "nt":
        fields = {}
        for line in Path("/proc/self/status").read_text(encoding="ascii").splitlines():
            key, _, value = line.partition(":")
            if key in {"VmRSS", "VmHWM"}:
                fields[key] = int(value.split()[0]) * 1024
        current = fields["VmRSS"]
        peak = fields["VmHWM"]
        return {
            "WorkingSetSize": current,
            "PeakWorkingSetSize": peak,
            "PrivateUsage": current,
        }

    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
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

    get_process = ctypes.windll.kernel32.GetCurrentProcess
    get_process.restype = wintypes.HANDLE
    get_memory = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(Counters),
        wintypes.DWORD,
    ]
    get_memory.restype = wintypes.BOOL
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    if not get_memory(get_process(), ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return {
        "WorkingSetSize": counters.WorkingSetSize,
        "PeakWorkingSetSize": counters.PeakWorkingSetSize,
        "PrivateUsage": counters.PrivateUsage,
    }


def _resource_child(
    *,
    policy: dict[str, Any],
    mode: str,
    storage: str,
    method: str,
    seconds: float,
    sample_seconds: float,
) -> dict[str, Any]:
    if mode == "legacy":
        storage_type = (
            LegacyMultiArray if storage == "MultiArray" else LegacyMutableMultiArray
        )
    else:
        storage_type = MultiArray if storage == "MultiArray" else MutableMultiArray
    count = policy["gated_count"]
    sources: list[tuple[Any, DynShape, Any]] = []
    for domain in policy["domains"]:
        data = _values(domain=domain, count=count, seed=policy["seed"] + count)
        for order in policy["orders"]:
            storage_order = StorageOrder[order]
            sources.append(
                (
                    storage_type(Shape2(2, count // 2, storage_order), data),
                    DynShape((count // 2, 2)),
                    method,
                )
            )

    def operate() -> None:
        for source, target, operation in sources:
            value = (
                source.reshape(target) if operation == "reshape" else source.flatten()
            )
            result = value if mode == "legacy" else value.unwrap()
            if result._data.size != count:
                raise AssertionError("resource operation published incomplete data")
            del result, value

    for _ in range(policy["resource_warmup"]):
        operate()
    warm = _memory()
    started = time.monotonic()
    next_sample = started
    samples: list[dict[str, int | float]] = []
    while True:
        for _ in range(policy["resource_batch_operations"]):
            operate()
        now = time.monotonic()
        if now >= next_sample:
            samples.append({**_memory(), "elapsed": now - started})
            next_sample = now + sample_seconds
        if now - started >= seconds:
            break

    growth = max(
        int(sample["PrivateUsage"]) - warm["PrivateUsage"] for sample in samples
    )
    peak_increment = (
        max(int(sample["PeakWorkingSetSize"]) for sample in samples)
        - warm["WorkingSetSize"]
    )
    return {
        "mode": mode,
        "storage": storage,
        "method": method,
        "seconds": time.monotonic() - started,
        "warm": warm,
        "samples": samples,
        "post_warmup_growth": growth,
        "peak_increment": peak_increment,
        "passed": growth <= policy["max_post_warmup_growth"]
        and peak_increment <= policy["max_peak_increment"],
    }


def _identity(*, extension_hash: str) -> dict[str, Any]:
    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python": sys.version,
        "numpy": np.__version__,
        "extension_sha256": extension_hash,
        "source_sha256": {
            "runner": _digest(Path(__file__)),
            "legacy": _digest(HERE / "legacy_storage_transform.py"),
            "policy": _digest(POLICY_PATH),
            "Cargo.lock": _digest(ROOT / "native" / "Cargo.lock"),
            "rust-toolchain.toml": _digest(ROOT / "rust-toolchain.toml"),
            "storage_transform.py": _digest(
                ROOT / "ospf_python" / "_binding" / "storage_transform.py"
            ),
            "multiarray.rs": _digest(ROOT / "native" / "src" / "multiarray.rs"),
        },
    }


def _assess(
    *,
    policy: dict[str, Any],
    rows: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    runner_matches: bool,
    extension_matches: bool,
    rounds: int,
    soak_seconds: float,
) -> dict[str, Any]:
    failures = [
        row
        for row in rows
        if row["count"] >= policy["gated_minimum"]
        and row["ratio"] > policy["threshold"]
    ]
    checks = {
        "declared_fixed_runner": runner_matches,
        "extension_hash_matches": extension_matches,
        "two_or_more_rounds": rounds >= 2,
        "ten_minute_soak": soak_seconds >= 600,
        "complete_96_row_matrix_per_round": len(rows)
        == policy["expected_rows"] * rounds,
        "no_gated_performance_failures": not failures,
        "eight_resource_scenarios": len(resources) == 8,
        "all_resource_envelopes_pass": len(resources) == 8
        and all(record["passed"] for record in resources),
    }
    return {
        "checks": checks,
        "gated_failures": failures,
        "accepted": all(checks.values()),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runner-id", default="")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--soak-seconds", type=float, default=30)
    parser.add_argument("--sample-seconds", type=float, default=2)
    parser.add_argument("--expected-extension-sha256", default="")
    parser.add_argument("--acceptance", action="store_true")
    parser.add_argument("--resource-child", action="store_true")
    parser.add_argument("--mode", choices=("legacy", "native"))
    parser.add_argument("--storage", choices=("MultiArray", "MutableMultiArray"))
    parser.add_argument("--method", choices=("reshape", "flatten"))
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    policy = _load_policy()
    output = args.output.resolve()
    if args.resource_child:
        if not args.mode or not args.storage or not args.method:
            raise SystemExit("resource child requires --mode, --storage and --method")
        output.parent.mkdir(parents=True, exist_ok=True)
        record = _resource_child(
            policy=policy,
            mode=args.mode,
            storage=args.storage,
            method=args.method,
            seconds=args.soak_seconds,
            sample_seconds=args.sample_seconds,
        )
        output.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return 0 if record["passed"] else 1

    output.mkdir(parents=True, exist_ok=True)
    native_file = Path(_native.__file__).resolve()
    extension_hash = _digest(native_file)
    runner_matches = bool(args.runner_id) and (
        os.environ.get("OSPF_STORAGE_FIXED_RUNNER") == args.runner_id
    )
    extension_matches = bool(args.expected_extension_sha256) and (
        args.expected_extension_sha256 == extension_hash
    )

    started = time.monotonic()
    # 诊断（只打日志，不改判据）：每轮前后记录存活块数与 RSS，用于定位 B446 观测到的跨轮退化。
    # Diagnostics only: block count and RSS before/after each round.
    rows = []
    for round_index in range(args.rounds):
        print(
            f"[diag] before round {round_index}: blocks={sys.getallocatedblocks():,} "
            f"rss={_rss_bytes():,}",
            flush=True,
        )
        rows.extend(_measure_round(policy=policy, round_index=round_index))
        print(
            f"[diag] after  round {round_index}: blocks={sys.getallocatedblocks():,} "
            f"rss={_rss_bytes():,}",
            flush=True,
        )
    (output / "performance.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )

    scenarios = [
        (mode, storage, method)
        for mode in ("legacy", "native")
        for storage in ("MultiArray", "MutableMultiArray")
        for method in ("reshape", "flatten")
    ]
    processes: list[tuple[subprocess.Popen[bytes], Path]] = []
    for mode, storage, method in scenarios:
        child_output = output / f"resource-{mode}-{storage}-{method}.json"
        child_log = output / f"resource-{mode}-{storage}-{method}.log"
        with child_log.open("wb") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--output",
                    str(child_output),
                    "--mode",
                    mode,
                    "--storage",
                    storage,
                    "--method",
                    method,
                    "--soak-seconds",
                    str(args.soak_seconds),
                    "--sample-seconds",
                    str(args.sample_seconds),
                    "--resource-child",
                ],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        processes.append((process, child_output))
    for process, child_output in processes:
        process.wait(timeout=args.soak_seconds + 180)
        if not child_output.exists():
            raise RuntimeError(
                f"resource child exited {process.returncode} without a report"
            )
    resources = [
        json.loads(child_output.read_text(encoding="utf-8"))
        for _, child_output in processes
    ]

    assessment = _assess(
        policy=policy,
        rows=rows,
        resources=resources,
        runner_matches=runner_matches,
        extension_matches=extension_matches,
        rounds=args.rounds,
        soak_seconds=args.soak_seconds,
    )
    report = {
        "policy": policy,
        "identity": _identity(extension_hash=extension_hash),
        "native_file": str(native_file),
        "elapsed_seconds": time.monotonic() - started,
        "rounds": args.rounds,
        "soak_seconds": args.soak_seconds,
        "rows": rows,
        "resources": resources,
        "assessment": assessment,
        "fixed_runner": runner_matches,
        "full_domain_budget_verified": assessment["accepted"],
        "long_term_resource_verified": assessment["accepted"],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "accepted": assessment["accepted"],
                "checks": assessment["checks"],
                "gated_failures": len(assessment["gated_failures"]),
                "rows": len(rows),
                "resources": len(resources),
                "extension_sha256": extension_hash,
                "report": str(output / "report.json"),
            },
            indent=2,
        )
    )
    if args.acceptance and not assessment["accepted"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
