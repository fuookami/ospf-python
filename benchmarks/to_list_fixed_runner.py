"""Fixed-runner acceptance for the public `to_list` entry points.

Mirrors `storage_transform_fixed_runner.py`: the complete matrix, seeded inputs,
ABBA/BAAB sampling, resource envelopes and a long soak are all pre-registered in
`to_list_fixed_runner_policy.json`. A report is accepted only when it is produced on
the declared runner against the pre-registered native extension, with two complete
performance rounds and at least ten minutes of resource soak.

Usage (local measurement):
    python benchmarks/to_list_fixed_runner.py --output logs/to-list-r1 --rounds 2 \
      --soak-seconds 620 --expected-extension-sha256 <sha256>

Usage (declared fixed runner):
    OSPF_TO_LIST_FIXED_RUNNER=ospf-win-cp313-v1 \
    python benchmarks/to_list_fixed_runner.py --output logs/to-list-r1 \
      --runner-id ospf-win-cp313-v1 --rounds 2 --soak-seconds 620 \
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
POLICY_PATH = HERE / "to_list_fixed_runner_policy.json"

sys.path.insert(0, str(HERE))

from legacy_to_list import (  # noqa: E402
    LegacyMultiArray,
    LegacyMutableMultiArray,
)


def _digest(path: Path) -> str:
    """计算文件摘要。 / Compute a file digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _policy() -> dict[str, Any]:
    """读取预注册政策。 / Read the pre-registered policy."""
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _build_data(count: int, domain: str) -> np.ndarray:
    """构造输入数据。 / Build the input data."""
    from ospf_python.quantities.quantity.quantity import Quantity
    from ospf_python.quantities.unit.length import METER

    if domain == "int16":
        return (np.arange(count) % 17).astype(np.int16)
    if domain == "float64":
        return (np.arange(count) % 17).astype(np.float64) / 8
    data = np.empty(count, dtype=object)
    for index in range(count):
        data[index] = (
            index % 17
            if domain == "object"
            else Quantity(Fraction(index % 17, 8), METER)
        )
    return data


def _flat_capacity(shapes: list[list[int]]) -> int:
    """取最大元素数，用于一次构造子进程输入。 / Largest element count for child input."""
    total = 1
    for dimension in shapes:
        product = 1
        for value in dimension:
            product *= value
        total = max(total, product)
    return total


def _timed(*, function: Any, repeats: int) -> float:
    """按批次计时并返回每次调用的纳秒数。 / Time a batch and return ns per call."""
    gc.collect()
    enabled = gc.isenabled()
    gc.disable()
    start = time.perf_counter_ns()
    try:
        for _ in range(repeats):
            value = function()
            del value
    finally:
        if enabled:
            gc.enable()
    return (time.perf_counter_ns() - start) / repeats


def _measure_round(policy: dict[str, Any], round_index: int) -> list[dict[str, Any]]:
    """跑一轮完整矩阵。 / Run one complete matrix pass."""
    from ospf_python.multiarray import (
        DynShape,
        MultiArray,
        MutableMultiArray,
        StorageOrder,
    )

    classes = {"MultiArray": MultiArray, "MutableMultiArray": MutableMultiArray}
    # 数据按 (shape, domain) 预构造并复用，避免 object/quantity 域反复造十万个叶子。
    # Build each (shape, domain) input once and reuse it across classes and rounds.
    cache: dict[tuple[int, str], Any] = {}
    rows: list[dict[str, Any]] = []
    for dimension in policy["shapes"]:
        count = 1
        for value in dimension:
            count *= value
        for domain in policy["domains"]:
            repeats = policy["repeats_by_domain_and_count"][domain][str(count)]
            key = (count, domain)
            if key not in cache:
                cache[key] = _build_data(count, domain)
            data = cache[key]
            for class_name in policy["classes"]:
                storage = classes[class_name]
                legacy_storage = (
                    LegacyMultiArray
                    if class_name == "MultiArray"
                    else LegacyMutableMultiArray
                )
                for layout in policy["layouts"]:
                    order = StorageOrder[layout]
                    shape = DynShape(tuple(dimension), order)
                    source = storage(shape, data)
                    old = legacy_storage(shape, data)
                    native = lambda source=source: source.to_list().unwrap()  # noqa: E731
                    legacy = lambda old=old: old.to_list()  # noqa: E731
                    rounds: list[float] = []
                    for sample_index in range(policy["alternating_rounds"]):
                        sequence = (
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
                        native_samples: list[float] = []
                        legacy_samples: list[float] = []
                        for mode, function in sequence:
                            sample = _timed(function=function, repeats=repeats)
                            if mode == "native":
                                native_samples.append(sample)
                            else:
                                legacy_samples.append(sample)
                        rounds.append(
                            statistics.median(native_samples)
                            / statistics.median(legacy_samples)
                        )
                    rows.append(
                        {
                            "shape": dimension,
                            "count": count,
                            "domain": domain,
                            "storage": class_name,
                            "order": layout,
                            "method": "to_list",
                            "ratio": statistics.median(rounds),
                            "round_ratios": rounds,
                            "round": round_index,
                        }
                    )
                    del source, old
    return rows


def _resource_child(
    output: Path,
    storage_name: str,
    policy: dict[str, Any],
    seconds: float,
    sample_seconds: float,
) -> int:
    """子进程：跑资源 soak。 / Child process: run the resource soak."""
    import ctypes
    from ctypes import wintypes

    from ospf_python.multiarray import (
        DynShape,
        MultiArray,
        MutableMultiArray,
        StorageOrder,
    )

    class _COUNTERS(ctypes.Structure):
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
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_COUNTERS),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    def memory() -> tuple[int, int]:
        counters = _COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        psapi.GetProcessMemoryInfo(
            kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
        )
        return counters.WorkingSetSize, counters.PeakWorkingSetSize

    dimension = policy["shapes"][0]
    count = 1
    for value in dimension:
        count *= value
    storage = {"MultiArray": MultiArray, "MutableMultiArray": MutableMultiArray}[
        storage_name
    ]
    shape = DynShape(tuple(dimension), StorageOrder.ROW_MAJOR)
    source = storage(shape, _build_data(count, "int16"))
    call = lambda: source.to_list().unwrap()  # noqa: E731
    for _ in range(policy["resource_warmup"]):
        value = call()
        del value
    baseline_ws, _ = memory()
    peak = baseline_ws
    started = time.monotonic()
    next_sample = started + sample_seconds
    operations = 0
    while time.monotonic() - started < seconds:
        for _ in range(policy["resource_batch_operations"]):
            value = call()
            del value
            operations += 1
        now = time.monotonic()
        if now >= next_sample:
            current, high = memory()
            peak = max(peak, high)
            next_sample = now + sample_seconds
    gc.collect()
    final_ws, _ = memory()
    record = {
        "storage": storage_name,
        "seconds": seconds,
        "operations": operations,
        "baseline_ws": baseline_ws,
        "peak_increment": peak - baseline_ws,
        "growth": final_ws - baseline_ws,
        "max_peak_increment": policy["max_peak_increment"],
        "max_post_warmup_growth": policy["max_post_warmup_growth"],
    }
    record["passed"] = (
        record["peak_increment"] <= policy["max_peak_increment"]
        and record["growth"] <= policy["max_post_warmup_growth"]
    )
    output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return 0 if record["passed"] else 1


def _assess(
    policy: dict[str, Any],
    rows: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    runner_matches: bool,
    extension_matches: bool,
    rounds: int,
    soak_seconds: float,
) -> dict[str, Any]:
    """按政策判定。 / Assess against the policy."""
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
        "ten_minute_soak": soak_seconds >= policy["soak_seconds_minimum"],
        "complete_matrix_per_round": len(rows) == policy["expected_rows"] * rounds,
        "no_gated_performance_failures": not failures,
        "all_resource_envelopes_pass": bool(resources)
        and all(r["passed"] for r in resources),
    }
    return {
        "checks": checks,
        "gated_failures": failures,
        "accepted": all(checks.values()),
    }


def _parse_args() -> argparse.Namespace:
    """解析命令行。 / Parse the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runner-id", default="")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--soak-seconds", type=float, default=30)
    parser.add_argument("--sample-seconds", type=float, default=2)
    parser.add_argument("--expected-extension-sha256", default="")
    parser.add_argument("--acceptance", action="store_true")
    parser.add_argument("--resource-child", action="store_true")
    parser.add_argument("--storage", choices=("MultiArray", "MutableMultiArray"))
    return parser.parse_args()


def main() -> int:
    """入口。 / Entry point."""
    args = _parse_args()
    policy = _policy()
    if args.resource_child:
        assert args.storage is not None
        return _resource_child(
            args.output, args.storage, policy, args.soak_seconds, args.sample_seconds
        )

    from ospf_python import _native

    output: Path = args.output
    output.mkdir(parents=True, exist_ok=True)
    native_file = Path(_native.__file__).resolve()
    extension_hash = _digest(native_file)
    runner_matches = bool(args.runner_id) and (
        os.environ.get("OSPF_TO_LIST_FIXED_RUNNER") == args.runner_id
    )
    extension_matches = bool(args.expected_extension_sha256) and (
        args.expected_extension_sha256 == extension_hash
    )

    started = time.monotonic()
    rows = [
        row
        for round_index in range(args.rounds)
        for row in _measure_round(policy, round_index)
    ]
    (output / "performance.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )

    processes: list[tuple[subprocess.Popen[bytes], Path]] = []
    for storage_name in policy["classes"]:
        child_output = output / f"resource-{storage_name}.json"
        child_log = output / f"resource-{storage_name}.log"
        with child_log.open("wb") as log:
            processes.append(
                (
                    subprocess.Popen(
                        [
                            sys.executable,
                            str(Path(__file__).resolve()),
                            "--output",
                            str(child_output),
                            "--storage",
                            storage_name,
                            "--soak-seconds",
                            str(args.soak_seconds),
                            "--sample-seconds",
                            str(args.sample_seconds),
                            "--resource-child",
                        ],
                        cwd=ROOT,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                    ),
                    child_output,
                )
            )
    for process, child_output in processes:
        process.wait(timeout=args.soak_seconds + 300)
        if not child_output.exists():
            raise RuntimeError(
                f"resource child exited {process.returncode} without a report"
            )
    resources = [json.loads(path.read_text(encoding="utf-8")) for _, path in processes]

    assessment = _assess(
        policy,
        rows,
        resources,
        runner_matches,
        extension_matches,
        args.rounds,
        args.soak_seconds,
    )
    report = {
        "policy": policy,
        "identity": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "python": sys.version,
            "numpy": np.__version__,
            "extension_sha256": extension_hash,
            "policy_sha256": _digest(POLICY_PATH),
        },
        "native_file": str(native_file),
        "elapsed_seconds": time.monotonic() - started,
        "rounds": args.rounds,
        "soak_seconds": args.soak_seconds,
        "rows": len(rows),
        "resources": resources,
        "assessment": assessment,
        "fixed_runner": runner_matches,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "accepted": assessment["accepted"],
                "checks": assessment["checks"],
                "gated_failures": len(assessment["gated_failures"]),
                "report": str(output / "report.json"),
            },
            indent=2,
        )
    )
    if args.acceptance:
        return 0 if assessment["accepted"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
