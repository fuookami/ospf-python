"""MAC optimization 测试 / MAC optimization tests.

覆盖 MAC 计算、CG 到 MAC 转换、优化变量/约束和
优化管线。
Covers MAC calculation, CG to MAC conversion,
optimization variables/constraints, and pipeline.
"""

from __future__ import annotations

import pytest

from examples.framework_demo.demo2.domain.mac.model.mac_aggregation import (
    MACAggregation,
)
from examples.framework_demo.demo2.domain.mac.model.mac_position import (
    MACPosition,
)
from examples.framework_demo.demo2.domain.mac.model.mac_result import (
    MACResult,
)
from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_result import (
    OptimizationResult,
)
from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_variable import (
    OptimizationVariable,
)


class TestMACResult:
    """MACResult 测试 / MAC result tests."""

    def test_chord_length(self) -> None:
        """弦长计算 / Chord length calculation."""
        r = MACResult.create(
            mac_value=8.0,
            leading_edge=20.0,
            trailing_edge=28.0,
            station=24.0,
        )
        assert r.chord_length == pytest.approx(8.0)

    def test_contains_station(self) -> None:
        """站位在 MAC 范围内 / Station within MAC range."""
        r = MACResult.create(
            mac_value=8.0,
            leading_edge=20.0,
            trailing_edge=28.0,
            station=24.0,
        )
        assert r.contains_station(24.0) is True
        assert r.contains_station(19.0) is False
        assert r.contains_station(29.0) is False
        assert r.contains_station(20.0) is True
        assert r.contains_station(28.0) is True


class TestMACPosition:
    """MACPosition 测试 / MAC position tests."""

    def test_forward_cg(self) -> None:
        """前重心 / Forward CG."""
        pos = MACPosition.create(
            fuselage_station=22.0,
            percent_mac=20.0,
            cg_arm=5.0,
        )
        assert pos.is_forward is True
        assert pos.is_aft is False

    def test_aft_cg(self) -> None:
        """后重心 / Aft CG."""
        pos = MACPosition.create(
            fuselage_station=26.0,
            percent_mac=35.0,
            cg_arm=7.0,
        )
        assert pos.is_aft is True
        assert pos.is_forward is False

    def test_normal_cg(self) -> None:
        """正常重心 / Normal CG."""
        pos = MACPosition.create(
            fuselage_station=24.0,
            percent_mac=28.0,
            cg_arm=6.0,
        )
        assert pos.is_forward is False
        assert pos.is_aft is False

    def test_with_fuselage_station(self) -> None:
        """更新机身站位 / Update fuselage station."""
        pos = MACPosition.create(
            fuselage_station=22.0,
            percent_mac=25.0,
            cg_arm=5.0,
        )
        new_pos = pos.with_fuselage_station(24.0)
        assert new_pos.fuselage_station == pytest.approx(24.0)
        assert pos.fuselage_station == pytest.approx(22.0)


class TestMACAggregation:
    """MACAggregation 测试 / MAC aggregation tests."""

    def test_empty_aggregation(self) -> None:
        """空聚合 / Empty aggregation."""
        agg = MACAggregation.empty(aircraft_type="B747")
        assert agg.count == 0
        assert agg.is_empty is True
        assert agg.primary is None

    def test_add_and_primary(self) -> None:
        """添加和主结果 / Add and primary."""
        r = MACResult.create(
            mac_value=8.0,
            leading_edge=20.0,
            trailing_edge=28.0,
            station=24.0,
        )
        agg = MACAggregation.empty(aircraft_type="B747").add(r)
        assert agg.count == 1
        assert agg.primary is r

    def test_largest_mac(self) -> None:
        """最大 MAC 值 / Largest MAC value."""
        r1 = MACResult.create(
            mac_value=7.0,
            leading_edge=20.0,
            trailing_edge=27.0,
            station=23.5,
        )
        r2 = MACResult.create(
            mac_value=9.0,
            leading_edge=21.0,
            trailing_edge=30.0,
            station=25.5,
        )
        agg = MACAggregation.create(
            results=(r1, r2),
            aircraft_type="B747",
        )
        assert agg.largest_mac() is r2

    def test_containing_station(self) -> None:
        """包含站位查找 / Containing station lookup."""
        r1 = MACResult.create(
            mac_value=8.0,
            leading_edge=20.0,
            trailing_edge=28.0,
            station=24.0,
        )
        r2 = MACResult.create(
            mac_value=6.0,
            leading_edge=30.0,
            trailing_edge=36.0,
            station=33.0,
        )
        agg = MACAggregation.create(
            results=(r1, r2),
            aircraft_type="B747",
        )
        found = agg.containing_station(25.0)
        assert len(found) == 1
        assert found[0] is r1


class TestOptimizationVariable:
    """OptimizationVariable 测试 / Variable tests."""

    def test_create_variable(self) -> None:
        """创建变量 / Create variable."""
        v = OptimizationVariable.create(
            name="cg_x",
            lower=18.0,
            upper=33.0,
            value=25.0,
        )
        assert v.name == "cg_x"
        assert v.range == pytest.approx(15.0)

    def test_non_negative(self) -> None:
        """非负变量 / Non-negative variable."""
        v = OptimizationVariable.non_negative(name="w")
        assert v.lower == 0.0
        assert v.upper == float("inf")

    def test_is_fixed(self) -> None:
        """固定变量 / Fixed variable."""
        fixed = OptimizationVariable.create(name="c", lower=5.0, upper=5.0, value=5.0)
        free = OptimizationVariable.create(name="x", lower=0.0, upper=10.0, value=5.0)
        assert fixed.is_fixed is True
        assert free.is_fixed is False

    def test_is_binary(self) -> None:
        """二值变量 / Binary variable."""
        b = OptimizationVariable.create(name="b", lower=0.0, upper=1.0, value=0.0)
        c = OptimizationVariable.create(name="c", lower=0.0, upper=10.0, value=5.0)
        assert b.is_binary is True
        assert c.is_binary is False

    def test_within_bounds(self) -> None:
        """界内检查 / Bounds check."""
        v = OptimizationVariable.create(name="x", lower=0.0, upper=100.0, value=50.0)
        assert v.is_within_bounds(50.0) is True
        assert v.is_within_bounds(-1.0) is False
        assert v.is_within_bounds(101.0) is False

    def test_with_value(self) -> None:
        """更新值 / Update value."""
        v = OptimizationVariable.create(name="x", lower=0.0, upper=100.0, value=50.0)
        v2 = v.with_value(75.0)
        assert v2.value == pytest.approx(75.0)
        assert v.value == pytest.approx(50.0)


class TestOptimizationResult:
    """OptimizationResult 测试 / Result tests."""

    def test_optimal_result(self) -> None:
        """最优解 / Optimal result."""
        r = OptimizationResult.create_optimal(
            objective_value=-12.5,
            solution={"cg_x": 25.0, "payload": 50_000.0},
            iterations=42,
        )
        assert r.is_optimal is True
        assert r.is_feasible is True
        assert r.variable_value("cg_x") == pytest.approx(25.0)

    def test_infeasible_result(self) -> None:
        """不可行 / Infeasible result."""
        r = OptimizationResult.create_infeasible(iterations=10)
        assert r.is_optimal is False
        assert r.is_feasible is False

    def test_unbounded_result(self) -> None:
        """无界 / Unbounded result."""
        r = OptimizationResult.create_unbounded(iterations=5)
        assert r.status == "unbounded"
        assert r.objective_value == float("inf")

    def test_unknown_is_feasible(self) -> None:
        """未知状态视为可行 / Unknown considered feasible."""
        r = OptimizationResult.create_unknown(iterations=100)
        assert r.is_feasible is True

    def test_variable_value_missing(self) -> None:
        """不存在变量返回 None / Missing variable returns None."""
        r = OptimizationResult.create_optimal(
            objective_value=0.0,
            solution={"x": 1.0},
            iterations=1,
        )
        assert r.variable_value("missing") is None
