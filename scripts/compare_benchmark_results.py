#!/usr/bin/env python3
"""基准结果比较脚本 / Benchmark results comparison script.

对齐 Kotlin compare-benchmark-results.ps1：比较两组 pytest-benchmark JSON 输出，
输出回归/改进表，阈值告警，退出码反映有无回归。

Aligned to Kotlin compare-benchmark-results.ps1: compares two pytest-benchmark
JSON outputs, outputs regression/improvement table with threshold alerts,
exit code reflects whether regressions exist.

Usage:
    python scripts/compare_benchmark_results.py <baseline.json> <current.json> [--threshold 15]

Exit codes:
    0: No regressions detected
    1: Regressions detected (exceeds threshold)
    2: Invalid arguments or file errors
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# 强制 UTF-8 输出（Windows 兼容）/ Force UTF-8 output (Windows compat)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


@dataclass(frozen=True)
class BenchmarkResult:
    """单个基准点结果 / Single benchmark point result.

    Attributes:
        name: 基准名称 / Benchmark name.
        mean: 平均耗时（秒）/ Mean time (seconds).
        stddev: 标准差 / Standard deviation.
        min_val: 最小值 / Minimum value.
        max_val: 最大值 / Maximum value.
        median: 中位数 / Median.
        rounds: 迭代次数 / Number of rounds.
    """

    name: str
    mean: float
    stddev: float
    min_val: float
    max_val: float
    median: float
    rounds: int


@dataclass(frozen=True)
class ComparisonResult:
    """单个基准点比较结果 / Single benchmark comparison result.

    Attributes:
        name: 基准名称 / Benchmark name.
        baseline_mean: 基线平均耗时 / Baseline mean time.
        current_mean: 当前平均耗时 / Current mean time.
        change_pct: 变化百分比 / Change percentage.
        is_regression: 是否为回归 / Whether it's a regression.
        is_improvement: 是否为改进 / Whether it's an improvement.
    """

    name: str
    baseline_mean: float
    current_mean: float
    change_pct: float
    is_regression: bool
    is_improvement: bool


def load_benchmarks(path: Path) -> dict[str, BenchmarkResult]:
    """加载基准结果 JSON / Load benchmark results JSON.

    Args:
        path: JSON 文件路径 / JSON file path.

    Returns:
        基准名称到结果的映射 / Mapping of benchmark name to result.

    Raises:
        FileNotFoundError: 文件不存在 / File not found.
        json.JSONDecodeError: JSON 解析错误 / JSON parse error.
    """
    with open(path) as f:
        data = json.load(f)

    results: dict[str, BenchmarkResult] = {}
    for bench in data.get("benchmarks", []):
        name = bench["name"]
        stats = bench["stats"]
        results[name] = BenchmarkResult(
            name=name,
            mean=stats["mean"],
            stddev=stats["stddev"],
            min_val=stats["min"],
            max_val=stats["max"],
            median=stats["median"],
            rounds=stats["rounds"],
        )
    return results


def compare_benchmarks(
    baseline: dict[str, BenchmarkResult],
    current: dict[str, BenchmarkResult],
    threshold_pct: float,
) -> list[ComparisonResult]:
    """比较两组基准结果 / Compare two benchmark results.

    Args:
        baseline: 基线结果 / Baseline results.
        current: 当前结果 / Current results.
        threshold_pct: 回归阈值百分比 / Regression threshold percentage.

    Returns:
        比较结果列表 / List of comparison results.
    """
    results: list[ComparisonResult] = []

    for name in sorted(set(baseline.keys()) | set(current.keys())):
        if name not in baseline:
            # 新增基准 / New benchmark
            results.append(
                ComparisonResult(
                    name=name,
                    baseline_mean=0.0,
                    current_mean=current[name].mean,
                    change_pct=float("inf"),
                    is_regression=False,
                    is_improvement=False,
                )
            )
            continue

        if name not in current:
            # 已删除基准 / Removed benchmark
            results.append(
                ComparisonResult(
                    name=name,
                    baseline_mean=baseline[name].mean,
                    current_mean=0.0,
                    change_pct=float("-inf"),
                    is_regression=False,
                    is_improvement=False,
                )
            )
            continue

        b_mean = baseline[name].mean
        c_mean = current[name].mean

        if b_mean == 0:
            change_pct = 0.0 if c_mean == 0 else float("inf")
        else:
            change_pct = ((c_mean - b_mean) / b_mean) * 100.0

        results.append(
            ComparisonResult(
                name=name,
                baseline_mean=b_mean,
                current_mean=c_mean,
                change_pct=change_pct,
                is_regression=change_pct > threshold_pct,
                is_improvement=change_pct < -threshold_pct,
            )
        )

    return results


def format_time(seconds: float) -> str:
    """格式化时间为人类可读格式 / Format time as human-readable.

    Args:
        seconds: 秒数 / Seconds.

    Returns:
        格式化时间字符串 / Formatted time string.
    """
    if seconds == 0:
        return "N/A"
    if seconds < 1e-6:
        return f"{seconds * 1e9:.1f}ns"
    if seconds < 1e-3:
        return f"{seconds * 1e6:.1f}µs"
    if seconds < 1.0:
        return f"{seconds * 1e3:.2f}ms"
    return f"{seconds:.3f}s"


def print_comparison_table(
    results: list[ComparisonResult],
    threshold_pct: float,
) -> bool:
    """打印比较结果表 / Print comparison results table.

    Args:
        results: 比较结果 / Comparison results.
        threshold_pct: 回归阈值 / Regression threshold.

    Returns:
        是否有回归 / Whether regressions exist.
    """
    has_regression = False

    # 分类 / Categorize
    regressions = [r for r in results if r.is_regression]
    improvements = [r for r in results if r.is_improvement]
    unchanged = [r for r in results if not r.is_regression and not r.is_improvement]

    print("=" * 90)
    print("Benchmark Comparison Results")
    print(f"Threshold: {threshold_pct}%")
    print("=" * 90)

    if regressions:
        has_regression = True
        print(f"\n[!] REGRESSIONS ({len(regressions)}):")
        print("-" * 90)
        print(f"{'Name':<50} {'Baseline':>12} {'Current':>12} {'Change':>10}")
        print("-" * 90)
        for r in regressions:
            print(
                f"{r.name:<50} "
                f"{format_time(r.baseline_mean):>12} "
                f"{format_time(r.current_mean):>12} "
                f"{r.change_pct:>+9.1f}%"
            )

    if improvements:
        print(f"\n[+] IMPROVEMENTS ({len(improvements)}):")
        print("-" * 90)
        print(f"{'Name':<50} {'Baseline':>12} {'Current':>12} {'Change':>10}")
        print("-" * 90)
        for r in improvements:
            print(
                f"{r.name:<50} "
                f"{format_time(r.baseline_mean):>12} "
                f"{format_time(r.current_mean):>12} "
                f"{r.change_pct:>+9.1f}%"
            )

    if unchanged:
        print(f"\n  UNCHANGED ({len(unchanged)}):")
        print("-" * 90)
        print(f"{'Name':<50} {'Baseline':>12} {'Current':>12} {'Change':>10}")
        print("-" * 90)
        for r in unchanged:
            print(
                f"{r.name:<50} "
                f"{format_time(r.baseline_mean):>12} "
                f"{format_time(r.current_mean):>12} "
                f"{r.change_pct:>+9.1f}%"
            )

    print("\n" + "=" * 90)
    print(
        f"Total: {len(results)} benchmarks, "
        f"{len(regressions)} regressions, "
        f"{len(improvements)} improvements, "
        f"{len(unchanged)} unchanged"
    )
    print("=" * 90)

    return has_regression


def main() -> int:
    """主入口 / Main entry point.

    Returns:
        退出码 / Exit code.
    """
    parser = argparse.ArgumentParser(
        description="比较两组 pytest-benchmark JSON 输出 / Compare two pytest-benchmark JSON outputs.",
    )
    parser.add_argument(
        "baseline",
        type=Path,
        help="基线 JSON 文件路径 / Baseline JSON file path.",
    )
    parser.add_argument(
        "current",
        type=Path,
        help="当前 JSON 文件路径 / Current JSON file path.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=15.0,
        help="回归阈值百分比（默认 15%）/ Regression threshold percentage (default 15%).",
    )

    args = parser.parse_args()

    if not args.baseline.exists():
        print(f"Error: Baseline file not found: {args.baseline}", file=sys.stderr)
        return 2
    if not args.current.exists():
        print(f"Error: Current file not found: {args.current}", file=sys.stderr)
        return 2

    try:
        baseline = load_benchmarks(args.baseline)
        current = load_benchmarks(args.current)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return 2

    if not baseline:
        print("Warning: Baseline file contains no benchmarks.", file=sys.stderr)
    if not current:
        print("Warning: Current file contains no benchmarks.", file=sys.stderr)

    results = compare_benchmarks(baseline, current, args.threshold)
    has_regression = print_comparison_table(results, args.threshold)

    return 1 if has_regression else 0


if __name__ == "__main__":
    sys.exit(main())
