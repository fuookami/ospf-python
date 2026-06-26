"""束编组解分析器额外测试 / Bunch solution analyzer extra tests.

补充覆盖 SolutionAnalyzer 的质量分析、可行性检查和
利用率计算方法。
Supplementary coverage for SolutionAnalyzer quality analysis,
feasibility checking, and utilization computation methods.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.service.solution_analyzer import (
    FeasibilityReport,
    SolutionAnalyzer,
    SolutionQuality,
)

# ==================== 辅助类型 / Helper types ====================


@dataclass(frozen=True)
class _FakeCapacity:
    """测试用容量记录。/ Test capacity record."""

    bunch_key: str
    max_capacity: float
    remaining_capacity: float


@dataclass(frozen=True)
class _FakeAssignment:
    """测试用分配记录。/ Test assignment record."""

    bunch_key: str
    item_key: str
    demand: float


@dataclass(frozen=True)
class _FakeAggregation:
    """测试用聚合。/ Test aggregation."""

    _bunch_keys: tuple[str, ...] = ()
    _capacities: tuple[_FakeCapacity, ...] = ()
    _assignments: tuple[_FakeAssignment, ...] = ()

    @property
    def bunch_keys(self) -> tuple[str, ...]:
        """获取束编组键。/ Get bunch keys."""
        return self._bunch_keys

    def get_capacity(self, bunch_key: str) -> _FakeCapacity | None:
        """获取容量。/ Get capacity."""
        for c in self._capacities:
            if c.bunch_key == bunch_key:
                return c
        return None

    def total_demand_for_bunch(self, bunch_key: str) -> float:
        """计算束编组总需求。/ Compute total demand for bunch."""
        return sum(a.demand for a in self._assignments if a.bunch_key == bunch_key)


# ==================== SolutionQuality 测试 ========================


class TestSolutionQuality:
    """SolutionQuality 数据类测试。/ SolutionQuality tests."""

    def test_default_values(self) -> None:
        """默认值测试。/ Default values test."""
        q = SolutionQuality()
        assert q.total_bunches == 0
        assert q.average_utilization == 0.0
        assert q.min_utilization == 0.0
        assert q.max_utilization == 0.0
        assert q.balance_score == 0.0

    def test_custom_values(self) -> None:
        """自定义值测试。/ Custom values test."""
        q = SolutionQuality(
            total_bunches=3,
            average_utilization=0.75,
            min_utilization=0.5,
            max_utilization=1.0,
            balance_score=0.5,
        )
        assert q.total_bunches == 3
        assert q.balance_score == 0.5


# ==================== FeasibilityReport 测试 ======================


class TestFeasibilityReport:
    """FeasibilityReport 数据类测试。/ FeasibilityReport tests."""

    def test_default_values(self) -> None:
        """默认值测试。/ Default values test."""
        r = FeasibilityReport()
        assert r.is_feasible is True
        assert r.capacity_violations == 0
        assert r.demand_violations == 0
        assert r.overloaded_bunches == ()

    def test_custom_values(self) -> None:
        """自定义值测试。/ Custom values test."""
        r = FeasibilityReport(
            is_feasible=False,
            capacity_violations=2,
            demand_violations=1,
            overloaded_bunches=("b1", "b2"),
        )
        assert r.is_feasible is False
        assert len(r.overloaded_bunches) == 2


# ==================== analyze_quality 测试 ========================


class TestAnalyzeQuality:
    """analyze_quality 方法测试。/ analyze_quality tests."""

    def test_empty_aggregation(self) -> None:
        """空聚合返回默认质量。/ Empty aggregation returns default."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation()
        q = analyzer.analyze_quality(agg)
        assert q.total_bunches == 0
        assert q.average_utilization == 0.0

    def test_single_bunch(self) -> None:
        """单束编组质量分析。/ Single bunch quality analysis."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1",),
            _assignments=(_FakeAssignment(bunch_key="b1", item_key="i1", demand=5.0),),
        )
        q = analyzer.analyze_quality(agg)
        assert q.total_bunches == 1
        assert q.average_utilization == 5.0
        assert q.min_utilization == 5.0
        assert q.max_utilization == 5.0

    def test_multiple_bunches_balanced(self) -> None:
        """多束编组均衡分析。/ Multiple bunches balanced analysis."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1", "b2"),
            _assignments=(
                _FakeAssignment(bunch_key="b1", item_key="i1", demand=5.0),
                _FakeAssignment(bunch_key="b2", item_key="i2", demand=5.0),
            ),
        )
        q = analyzer.analyze_quality(agg)
        assert q.total_bunches == 2
        assert q.average_utilization == 5.0
        assert q.balance_score >= 0.0

    def test_multiple_bunches_unbalanced(self) -> None:
        """多束编组不均衡分析。/ Multiple bunches unbalanced analysis."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1", "b2"),
            _assignments=(
                _FakeAssignment(bunch_key="b1", item_key="i1", demand=1.0),
                _FakeAssignment(bunch_key="b2", item_key="i2", demand=9.0),
            ),
        )
        q = analyzer.analyze_quality(agg)
        assert q.total_bunches == 2
        assert q.min_utilization == 1.0
        assert q.max_utilization == 9.0
        assert q.balance_score < 1.0

    def test_custom_tolerance(self) -> None:
        """自定义容差。/ Custom tolerance."""
        analyzer = SolutionAnalyzer(tolerance=1e-3)
        agg = _FakeAggregation(
            _bunch_keys=("b1",),
            _assignments=(_FakeAssignment(bunch_key="b1", item_key="i1", demand=5.0),),
        )
        q = analyzer.analyze_quality(agg)
        assert q.total_bunches == 1


# ==================== check_feasibility 测试 ======================


class TestCheckFeasibility:
    """check_feasibility 方法测试。/ check_feasibility tests."""

    def test_empty_aggregation_feasible(self) -> None:
        """空聚合可行。/ Empty aggregation feasible."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation()
        report = analyzer.check_feasibility(agg)
        assert report.is_feasible is True

    def test_within_capacity_feasible(self) -> None:
        """容量内可行。/ Within capacity feasible."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1",),
            _capacities=(
                _FakeCapacity(
                    bunch_key="b1",
                    max_capacity=10.0,
                    remaining_capacity=5.0,
                ),
            ),
            _assignments=(_FakeAssignment(bunch_key="b1", item_key="i1", demand=5.0),),
        )
        report = analyzer.check_feasibility(agg)
        assert report.is_feasible is True
        assert report.capacity_violations == 0

    def test_exceeds_capacity_infeasible(self) -> None:
        """超容量不可行。/ Exceeds capacity infeasible."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1",),
            _capacities=(
                _FakeCapacity(
                    bunch_key="b1",
                    max_capacity=5.0,
                    remaining_capacity=0.0,
                ),
            ),
            _assignments=(_FakeAssignment(bunch_key="b1", item_key="i1", demand=10.0),),
        )
        report = analyzer.check_feasibility(agg)
        assert report.is_feasible is False
        assert report.capacity_violations == 1
        assert "b1" in report.overloaded_bunches

    def test_demand_violation(self) -> None:
        """需求违反检测。/ Demand violation detection."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1",),
            _capacities=(
                _FakeCapacity(
                    bunch_key="b1",
                    max_capacity=20.0,
                    remaining_capacity=3.0,
                ),
            ),
            _assignments=(_FakeAssignment(bunch_key="b1", item_key="i1", demand=5.0),),
        )
        report = analyzer.check_feasibility(agg)
        # demand(5) > remaining(3) => demand violation
        assert report.demand_violations >= 1

    def test_no_capacity_record_skips(self) -> None:
        """无容量记录时跳过检查。/ No capacity record skips check."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1",),
            _assignments=(_FakeAssignment(bunch_key="b1", item_key="i1", demand=5.0),),
        )
        report = analyzer.check_feasibility(agg)
        assert report.is_feasible is True


# ==================== compute_utilization 测试 ====================


class TestComputeUtilization:
    """compute_utilization 方法测试。/ compute_utilization tests."""

    def test_empty_aggregation(self) -> None:
        """空聚合返回空利用率。/ Empty aggregation returns empty."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation()
        result = analyzer.compute_utilization(agg)
        assert result == {}

    def test_with_capacity(self) -> None:
        """有容量时计算利用率。/ With capacity computes utilization."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1",),
            _capacities=(
                _FakeCapacity(
                    bunch_key="b1",
                    max_capacity=10.0,
                    remaining_capacity=5.0,
                ),
            ),
            _assignments=(_FakeAssignment(bunch_key="b1", item_key="i1", demand=5.0),),
        )
        result = analyzer.compute_utilization(agg)
        assert result["b1"] == 0.5

    def test_capped_at_one(self) -> None:
        """利用率上限为 1.0。/ Utilization capped at 1.0."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1",),
            _capacities=(
                _FakeCapacity(
                    bunch_key="b1",
                    max_capacity=5.0,
                    remaining_capacity=0.0,
                ),
            ),
            _assignments=(_FakeAssignment(bunch_key="b1", item_key="i1", demand=10.0),),
        )
        result = analyzer.compute_utilization(agg)
        assert result["b1"] == 1.0

    def test_no_capacity_returns_zero(self) -> None:
        """无容量记录返回 0。/ No capacity returns 0."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1",),
        )
        result = analyzer.compute_utilization(agg)
        assert result["b1"] == 0.0


# ==================== overloaded_bunches 测试 ====================


class TestOverloadedBunches:
    """overloaded_bunches 方法测试。/ overloaded_bunches tests."""

    def test_empty_returns_empty(self) -> None:
        """空聚合返回空元组。/ Empty returns empty tuple."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation()
        result = analyzer.overloaded_bunches(agg)
        assert result == ()

    def test_overloaded_detected(self) -> None:
        """超载检测正确。/ Overloaded detection correct."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1", "b2"),
            _capacities=(
                _FakeCapacity(
                    bunch_key="b1",
                    max_capacity=5.0,
                    remaining_capacity=0.0,
                ),
                _FakeCapacity(
                    bunch_key="b2",
                    max_capacity=10.0,
                    remaining_capacity=5.0,
                ),
            ),
            _assignments=(
                _FakeAssignment(bunch_key="b1", item_key="i1", demand=10.0),
                _FakeAssignment(bunch_key="b2", item_key="i2", demand=5.0),
            ),
        )
        result = analyzer.overloaded_bunches(agg)
        assert "b1" in result
        assert "b2" not in result

    def test_no_overloaded(self) -> None:
        """无超载返回空。/ No overloaded returns empty."""
        analyzer = SolutionAnalyzer()
        agg = _FakeAggregation(
            _bunch_keys=("b1",),
            _capacities=(
                _FakeCapacity(
                    bunch_key="b1",
                    max_capacity=10.0,
                    remaining_capacity=5.0,
                ),
            ),
            _assignments=(_FakeAssignment(bunch_key="b1", item_key="i1", demand=5.0),),
        )
        result = analyzer.overloaded_bunches(agg)
        assert result == ()
