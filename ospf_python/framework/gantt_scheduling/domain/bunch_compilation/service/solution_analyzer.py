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

        utilizations = tuple(
            aggregation.total_demand_for_bunch(bk) for bk in bunch_keys
        )
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

        for bunch_key in aggregation.bunch_keys:
            cap = aggregation.get_capacity(bunch_key)
            if cap is not None:
                demand = aggregation.total_demand_for_bunch(
                    bunch_key,
                )
                if demand > cap.max_capacity + self.tolerance:
                    cap_violations += 1
                    overloaded.append(bunch_key)
                if demand > cap.remaining_capacity + self.tolerance:
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
        for bunch_key in aggregation.bunch_keys:
            cap = aggregation.get_capacity(bunch_key)
            if cap is not None and cap.max_capacity > 0.0:
                demand = aggregation.total_demand_for_bunch(
                    bunch_key,
                )
                result[bunch_key] = min(
                    1.0,
                    demand / cap.max_capacity,
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
