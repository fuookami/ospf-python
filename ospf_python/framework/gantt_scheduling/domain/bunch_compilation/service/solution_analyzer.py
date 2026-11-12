"""束编组解分析器 / Bunch compilation solution analyzer.

分析束编组优化求解结果，提供可行性和质量评估。
Analyzes bunch compilation optimization results, providing
feasibility and quality assessment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_aggregation import (
        BunchCompilationAggregation,
    )


def _index_by_bunch(
    aggregation: BunchCompilationAggregation,
) -> tuple[dict[str, object], dict[str, float]]:
    """为每个束编组标识一次性取到容量与总需求。

    Resolve capacity and total demand once per bunch key.

    本模块的三个分析入口（`check_feasibility` / `compute_utilization` /
    `analyze_quality`）原本对每个束编组各调用一次 `get_capacity(...)` 与
    `total_demand_for_bunch(...)`，而那两个访问器各自全量扫一遍容量元组与分配元组，
    于是总复杂度是 O(束 × 分配)。500 个束时 `check_feasibility` 要 53 ms、
    `compute_utilization` 要 57 ms。

    这里对每个键**只查一次**，仍然走聚合类原有的公开访问器——不要求聚合暴露新的
    属性名，因此对既有替身（只实现了 `bunch_keys` / `get_capacity` /
    `total_demand_for_bunch`）也成立。语义与逐项查询完全相同。

    Each key is queried once, still through the aggregation's existing public accessors —
    no new attribute is required, so existing stand-ins that only implement
    `bunch_keys` / `get_capacity` / `total_demand_for_bunch` keep working.

    Returns:
        (束编组 → 容量, 束编组 → 总需求) / (bunch to capacity, bunch to total demand).

    **为什么用聚合类的原始元组而不是逐键访问器**：`total_demand_for_bunch(k)` 本身是
    O(分配)，逐键调用仍是 O(束 × 分配)——实测 500 束时 `check_feasibility` 25.7 ms，
    只比原来的 53.6 ms 快一倍。真正的 O(束 + 分配) 需要一次遍历原始元组。

    **为什么这不破坏既有替身**：本模块的替身（`_FakeAggregation`）实现了
    `bunch_keys` / `get_capacity` / `total_demand_for_bunch`，但没有 `capacities` /
    `assignments`。所以这里先试原始元组，**取不到就退回逐键访问器**——两条路语义相同，
    只是复杂度不同。这样既拿到真实类上的线性复杂度，也不要求替身实现更多属性。

    Uses the aggregation's raw tuples when available (true O(bunches + assignments)) and
    falls back to the per-key accessors otherwise, so existing stand-ins keep working.
    """
    capacities_raw = getattr(aggregation, "capacities", None)
    assignments_raw = getattr(aggregation, "assignments", None)

    if capacities_raw is None or assignments_raw is None:
        # 退回逐键访问器 / Fall back to the per-key accessors.
        capacities: dict[str, object] = {}
        demands: dict[str, float] = {}
        for bunch_key in aggregation.bunch_keys:
            demands[bunch_key] = aggregation.total_demand_for_bunch(bunch_key)
            capacity = aggregation.get_capacity(bunch_key)
            if capacity is not None:
                capacities[bunch_key] = capacity
        return capacities, demands

    # 一次遍历建索引：容量取首个匹配（与 `get_capacity` 一致），需求按顺序累加
    # （与 `total_demand_for_bunch` 的 `sum(...)` 一致）。
    # One pass: first capacity match (as `get_capacity`), demand summed in order.
    capacities = {}
    for capacity in capacities_raw:
        key = getattr(capacity, "bunch_key", None)
        if key is not None:
            capacities.setdefault(key, capacity)

    demands = {}
    for assignment in assignments_raw:
        key = getattr(assignment, "bunch_key", None)
        if key is not None:
            demands[key] = demands.get(key, 0.0) + getattr(assignment, "demand", 0.0)
    return capacities, demands


@dataclass(frozen=True)
class SolutionQuality:
    """解质量指标 / Solution quality metrics.

    Attributes:
        total_bunches: 束编组总数 / Total bunch count.
        average_utilization: 平均利用率 / Average utilization.
        min_utilization: 最低利用率 / Minimum utilization.
        max_utilization: 最高利用率 / Maximum utilization.
        balance_score: 均衡得分 (0.0-1.0) / Balance score.
    """

    total_bunches: int = 0
    average_utilization: float = 0.0
    min_utilization: float = 0.0
    max_utilization: float = 0.0
    balance_score: float = 0.0


@dataclass(frozen=True)
class FeasibilityReport:
    """可行性报告 / Feasibility report.

    Attributes:
        is_feasible: 是否可行 / Whether feasible.
        capacity_violations: 容量违反数 / Capacity violations.
        demand_violations: 需求数违反数 / Demand violations.
        overloaded_bunches: 超载束编组列表 /
            Overloaded bunch list.
    """

    is_feasible: bool = True
    capacity_violations: int = 0
    demand_violations: int = 0
    overloaded_bunches: tuple[str, ...] = ()


@dataclass(frozen=True)
class SolutionAnalyzer:
    """束编组解分析器 / Bunch compilation solution analyzer.

    对束编组优化结果进行全面分析，包括可行性检查、
    利用率统计和均衡性评估。
    Performs comprehensive analysis on bunch compilation
    results, including feasibility checks, utilization
    statistics, and balance assessment.

    Attributes:
        tolerance: 数值容差 / Numerical tolerance.
    """

    tolerance: float = 1e-6

    def analyze_quality(
        self,
        aggregation: BunchCompilationAggregation,
    ) -> SolutionQuality:
        """分析解质量 / Analyze solution quality.

        Args:
            aggregation: 束编组聚合。/ Bunch compilation aggregation.

        Returns:
            解质量指标。/ Solution quality metrics.
        """
        bunch_keys = aggregation.bunch_keys
        if not bunch_keys:
            return SolutionQuality()

        # `analyze_quality` 只关心需求，不关心容量。用同一个索引函数取需求：
        # 真实类走原始元组一次遍历，替身退回逐键访问器（两条路都填充全部键的需求）。
        # `analyze_quality` needs demand only; reuse the same index helper. Both branches
        # populate demand for every bunch key.
        _, demands = _index_by_bunch(aggregation)
        utilizations = tuple(demands.get(bk, 0.0) for bk in bunch_keys)
        avg = sum(utilizations) / len(utilizations)
        min_u = min(utilizations)
        max_u = max(utilizations)
        balance = 1.0 - (max_u - min_u) / max(avg, self.tolerance)
        return SolutionQuality(
            total_bunches=len(bunch_keys),
            average_utilization=avg,
            min_utilization=min_u,
            max_utilization=max_u,
            balance_score=max(0.0, min(1.0, balance)),
        )

    def check_feasibility(
        self,
        aggregation: BunchCompilationAggregation,
    ) -> FeasibilityReport:
        """检查可行性 / Check feasibility.

        Args:
            aggregation: 束编组聚合。/ Bunch compilation aggregation.

        Returns:
            可行性报告。/ Feasibility report.
        """
        cap_violations = 0
        demand_violations = 0
        overloaded: list[str] = []

        # 一次遍历建索引，而不是对每个束编组各调用两个 O(n) 访问器。
        # One index pass instead of two O(n) accessors per bunch.
        capacities, demands = _index_by_bunch(aggregation)
        for bunch_key in aggregation.bunch_keys:
            cap = capacities.get(bunch_key)
            if cap is not None:
                demand = demands.get(bunch_key, 0.0)
                if demand > cap.max_capacity + self.tolerance:  # type: ignore[attr-defined]
                    cap_violations += 1
                    overloaded.append(bunch_key)
                if demand > cap.remaining_capacity + self.tolerance:  # type: ignore[attr-defined]
                    demand_violations += 1

        return FeasibilityReport(
            is_feasible=(cap_violations == 0 and demand_violations == 0),
            capacity_violations=cap_violations,
            demand_violations=demand_violations,
            overloaded_bunches=tuple(overloaded),
        )

    def compute_utilization(
        self,
        aggregation: BunchCompilationAggregation,
    ) -> dict[str, float]:
        """计算各束编组利用率。

        Compute utilization for each bunch.

        Args:
            aggregation: 束编组聚合。/ Bunch compilation aggregation.

        Returns:
            束编组标识到利用率的映射。
            Mapping from bunch key to utilization rate.
        """
        result: dict[str, float] = {}
        # 一次遍历建索引，而不是对每个束编组各调用两个 O(n) 访问器。
        # One index pass instead of two O(n) accessors per bunch.
        capacities, demands = _index_by_bunch(aggregation)
        for bunch_key in aggregation.bunch_keys:
            cap = capacities.get(bunch_key)
            if cap is not None and cap.max_capacity > 0.0:  # type: ignore[attr-defined]
                demand = demands.get(bunch_key, 0.0)
                result[bunch_key] = min(
                    1.0,
                    demand / cap.max_capacity,  # type: ignore[attr-defined]
                )
            else:
                result[bunch_key] = 0.0
        return result

    def overloaded_bunches(
        self,
        aggregation: BunchCompilationAggregation,
    ) -> tuple[str, ...]:
        """获取超载的束编组 / Get overloaded bunches.

        Args:
            aggregation: 束编组聚合。/ Bunch compilation aggregation.

        Returns:
            超载的束编组标识元组。/ Tuple of overloaded bunch keys.
        """
        report = self.check_feasibility(aggregation)
        return report.overloaded_bunches
