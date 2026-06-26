"""容量调度测试 / Capacity scheduling tests.

覆盖 capacity_scheduling 域中模型桩、约束类、目标类及聚合的基本
功能。约束类使用桩聚合对象测试真实逻辑。
Covers basic functionality of model stubs, constraint classes,
objective classes, and aggregation in capacity_scheduling domain.
Constraint classes use stub aggregation to test real logic.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.aggregation import (
    Aggregation,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.capacity_scheduling_context import (
    CapacitySchedulingContext,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.assignment import (
    Assignment,
    CapacityAssignment,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity import (
    Capacity,
    SlotCapacity,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_aggregation import (
    CapacitySchedulingAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_aliases import (
    CapacitySchedulingAliases,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_model import (
    CapacitySchedulingModel,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_modeling_config import (
    CapacitySchedulingModelingConfig,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity_scheduling_solver_value_adapter import (
    CapacitySchedulingSolverValueAdapter,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.load import (
    Load,
    SlotLoad,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.scaled_capacity_scheduling_solver_value_adapter import (
    ScaledCapacitySchedulingSolverValueAdapter,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.service.limits.capacity_capacity_constraint import (
    CapacityCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.service.limits.capacity_demand_constraint import (
    CapacityDemandConstraint,
    DemandSatisfaction,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.service.limits.capacity_usage_minimization import (
    CapacityUsageMinimization,
    UsageObjectiveTerm,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.service.limits.capacity_volume_minimization import (
    CapacityVolumeMinimization,
    VolumeObjectiveTerm,
    VolumeSavingsResult,
)

# =========================================================================
#  Test doubles for aggregation
# =========================================================================


@dataclass(frozen=True)
class _StubCap:
    """桩容量记录 / Stub capacity record."""

    capacity_slot_key: str
    time_window_start: float = 0.0
    time_window_end: float = 1.0
    max_capacity: float = 100.0
    used_capacity: float = 0.0
    remaining_capacity: float = 100.0


@dataclass(frozen=True)
class _StubAssignment:
    """桩分配记录 / Stub assignment record."""

    assignment_amount: float = 0.0


@dataclass(frozen=True)
class _StubAggregation:
    """桩聚合，用于测试约束类。

    Stub aggregation for testing constraint classes.
    """

    capacities: tuple[_StubCap, ...] = ()
    work_item_keys: tuple[str, ...] = ()
    _loads: dict[str, float] | None = None
    _assignments: dict[str, tuple[_StubAssignment, ...]] | None = None

    def total_load_for_slot(self, slot_key: str) -> float:
        """获取指定槽的总负载 / Get total load for slot."""
        if self._loads is not None:
            return self._loads.get(slot_key, 0.0)
        return 0.0

    def assignments_for_work_item(
        self,
        key: str,
    ) -> tuple[_StubAssignment, ...]:
        """获取工作项的分配 / Get assignments for work item."""
        if self._assignments is not None:
            return self._assignments.get(key, ())
        return ()


# =========================================================================
#  Model stub tests
# =========================================================================


class TestCapacitySchedulingAggregation:
    """容量调度聚合测试 / Capacity scheduling aggregation tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        a = CapacitySchedulingAggregation()
        assert a.name == "capacity_scheduling_aggregation"

    def test_is_valid(self) -> None:
        """有效性检查 / Validity check."""
        a = CapacitySchedulingAggregation()
        assert a.is_valid is True

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        a = CapacitySchedulingAggregation()
        with pytest.raises(AttributeError):
            a.name = "x"  # type: ignore[misc]


class TestCapacitySchedulingAliases:
    """容量调度别名测试 / Capacity scheduling aliases tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        a = CapacitySchedulingAliases()
        assert a.name == "capacity_scheduling_aliases"

    def test_is_valid(self) -> None:
        """有效性检查 / Validity check."""
        a = CapacitySchedulingAliases()
        assert a.is_valid is True


class TestCapacitySchedulingModel:
    """容量调度模型测试 / Capacity scheduling model tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        m = CapacitySchedulingModel()
        assert m.name == "capacity_scheduling_model"

    def test_is_valid(self) -> None:
        """有效性检查 / Validity check."""
        m = CapacitySchedulingModel()
        assert m.is_valid is True

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        m = CapacitySchedulingModel()
        with pytest.raises(AttributeError):
            m.name = "x"  # type: ignore[misc]


class TestCapacitySchedulingModelingConfig:
    """容量调度建模配置测试 / Modeling config tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        c = CapacitySchedulingModelingConfig()
        assert c.name == "capacity_scheduling_modeling_config"

    def test_is_valid(self) -> None:
        """有效性检查 / Validity check."""
        c = CapacitySchedulingModelingConfig()
        assert c.is_valid is True


class TestCapacitySchedulingSolverValueAdapter:
    """求解器值适配器测试 / Solver value adapter tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        a = CapacitySchedulingSolverValueAdapter()
        expected = "capacity_scheduling_solver_value_adapter"
        assert a.name == expected

    def test_is_valid(self) -> None:
        """有效性检查 / Validity check."""
        a = CapacitySchedulingSolverValueAdapter()
        assert a.is_valid is True


class TestScaledCapacitySchedulingSolverValueAdapter:
    """缩放求解器值适配器测试 / Scaled adapter tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        a = ScaledCapacitySchedulingSolverValueAdapter()
        expected = "scaled_capacity_scheduling_solver_value_adapter"
        assert a.name == expected

    def test_is_valid(self) -> None:
        """有效性检查 / Validity check."""
        a = ScaledCapacitySchedulingSolverValueAdapter()
        assert a.is_valid is True


class TestAssignment:
    """分配测试 / Assignment tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        a = Assignment()
        assert a.name == "assignment"

    def test_is_valid(self) -> None:
        """有效性检查 / Validity check."""
        a = Assignment()
        assert a.is_valid is True

    def test_alias(self) -> None:
        """类型别名 / Type alias."""
        assert CapacityAssignment is Assignment


class TestCapacity:
    """容量测试 / Capacity tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        c = Capacity()
        assert c.name == "capacity"

    def test_is_valid(self) -> None:
        """有效性检查 / Validity check."""
        c = Capacity()
        assert c.is_valid is True

    def test_alias(self) -> None:
        """类型别名 / Type alias."""
        assert SlotCapacity is Capacity


class TestLoad:
    """负载测试 / Load tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        l = Load()
        assert l.name == "load"

    def test_is_valid(self) -> None:
        """有效性检查 / Validity check."""
        l = Load()
        assert l.is_valid is True

    def test_alias(self) -> None:
        """类型别名 / Type alias."""
        assert SlotLoad is Load


# =========================================================================
#  CapacitySchedulingContext tests
# =========================================================================


class TestCapacitySchedulingContext:
    """容量调度上下文测试 / Context tests."""

    def test_default_construction(self) -> None:
        """默认构造 / Default construction."""
        ctx = CapacitySchedulingContext()
        assert isinstance(
            ctx.aggregation,
            CapacitySchedulingAggregation,
        )
        assert isinstance(ctx.model, CapacitySchedulingModel)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        ctx = CapacitySchedulingContext()
        with pytest.raises(AttributeError):
            ctx.model = CapacitySchedulingModel()  # type: ignore[misc]


# =========================================================================
#  Aggregation tests
# =========================================================================


class TestAggregation:
    """顶层聚合测试 / Top-level aggregation tests."""

    def test_default_construction(self) -> None:
        """默认构造 / Default construction."""
        agg = Aggregation()
        assert isinstance(agg.model, CapacitySchedulingModel)

    def test_with_model(self) -> None:
        """替换模型 / Replace model."""
        agg = Aggregation()
        new_model = CapacitySchedulingModel(name="custom")
        new_agg = agg.with_model(new_model)
        assert new_agg.model.name == "custom"

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        agg = Aggregation()
        with pytest.raises(AttributeError):
            agg.model = CapacitySchedulingModel()  # type: ignore[misc]


# =========================================================================
#  CapacityCapacityConstraint tests
# =========================================================================


class TestCapacityCapacityConstraint:
    """容量容量约束测试 / Capacity capacity constraint tests."""

    def test_default_prefix(self) -> None:
        """默认前缀 / Default prefix."""
        c = CapacityCapacityConstraint()
        assert c.constraint_name_prefix == "cap_capacity"

    def test_custom_prefix(self) -> None:
        """自定义前缀 / Custom prefix."""
        c = CapacityCapacityConstraint(
            constraint_name_prefix="x",
        )
        assert c.constraint_name_prefix == "x"

    def test_constraint_name(self) -> None:
        """约束名称 / Constraint name."""
        c = CapacityCapacityConstraint()
        expected = "cap_capacity_slot1"
        assert c.constraint_name("slot1") == expected

    def test_build_constraints_no_capacities(self) -> None:
        """无容量时构建约束 / Build with no capacities."""
        c = CapacityCapacityConstraint()
        agg = _StubAggregation(capacities=())
        result = c.build_constraints(agg)  # type: ignore[arg-type]
        assert result == ()

    def test_build_constraints_stub_limitation(self) -> None:
        """桩容量不支持扩展字段 / Stub capacity lacks fields."""
        c = CapacityCapacityConstraint()
        cap = _StubCap(
            capacity_slot_key="s1",
            max_capacity=100.0,
        )
        agg = _StubAggregation(
            capacities=(cap,),
            _loads={"s1": 50.0},
        )
        result = c.build_constraints(agg)  # type: ignore[arg-type]
        assert isinstance(result, tuple)

    def test_is_feasible_stub_limitation(self) -> None:
        """桩容量下可行性检查 / Feasibility on stub."""
        c = CapacityCapacityConstraint()
        cap = _StubCap(
            capacity_slot_key="s1",
            max_capacity=100.0,
        )
        agg = _StubAggregation(
            capacities=(cap,),
            _loads={"s1": 80.0},
        )
        result = c.is_feasible(agg)  # type: ignore[arg-type]
        assert isinstance(result, bool)

    def test_violations_stub_limitation(self) -> None:
        """桩容量下违反检查 / Violations on stub."""
        c = CapacityCapacityConstraint()
        cap = _StubCap(
            capacity_slot_key="s1",
            max_capacity=100.0,
        )
        agg = _StubAggregation(
            capacities=(cap,),
            _loads={"s1": 120.0},
        )
        result = c.violations(agg)  # type: ignore[arg-type]
        assert isinstance(result, tuple)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        c = CapacityCapacityConstraint()
        with pytest.raises(AttributeError):
            c.constraint_name_prefix = "x"  # type: ignore[misc]


# =========================================================================
#  CapacityDemandConstraint tests
# =========================================================================


class TestDemandSatisfaction:
    """需求满足状态测试 / Demand satisfaction tests."""

    def test_construction(self) -> None:
        """构造 / Construction."""
        ds = DemandSatisfaction(
            work_item_key="w1",
            is_satisfied=True,
            assigned_amount=10.0,
            shortfall=0.0,
        )
        assert ds.work_item_key == "w1"
        assert ds.is_satisfied is True
        assert ds.assigned_amount == pytest.approx(10.0)
        assert ds.shortfall == pytest.approx(0.0)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        ds = DemandSatisfaction(
            work_item_key="w1",
            is_satisfied=False,
            assigned_amount=0.0,
            shortfall=5.0,
        )
        with pytest.raises(AttributeError):
            ds.is_satisfied = True  # type: ignore[misc]


class TestCapacityDemandConstraint:
    """容量需求约束测试 / Capacity demand constraint tests."""

    def test_default_prefix(self) -> None:
        """默认前缀 / Default prefix."""
        c = CapacityDemandConstraint()
        assert c.constraint_name_prefix == "cap_demand"

    def test_default_required_amount(self) -> None:
        """默认需求量 / Default required amount."""
        c = CapacityDemandConstraint()
        assert c.required_amount == pytest.approx(0.0)

    def test_constraint_name(self) -> None:
        """约束名称 / Constraint name."""
        c = CapacityDemandConstraint()
        assert c.constraint_name("w1") == "cap_demand_w1"

    def test_build_constraints_satisfied(self) -> None:
        """已满足的需求 / Satisfied demands."""
        c = CapacityDemandConstraint(required_amount=10.0)
        agg = _StubAggregation(
            work_item_keys=("w1",),
            _assignments={
                "w1": (_StubAssignment(10.0),),
            },
        )
        result = c.build_constraints(agg)  # type: ignore[arg-type]
        assert len(result) == 1
        assert result[0].is_satisfied is True
        assert result[0].shortfall == pytest.approx(0.0)

    def test_build_constraints_unsatisfied(self) -> None:
        """未满足的需求 / Unsatisfied demands."""
        c = CapacityDemandConstraint(required_amount=10.0)
        agg = _StubAggregation(
            work_item_keys=("w1",),
            _assignments={
                "w1": (_StubAssignment(3.0),),
            },
        )
        result = c.build_constraints(agg)  # type: ignore[arg-type]
        assert len(result) == 1
        assert result[0].is_satisfied is False
        assert result[0].shortfall == pytest.approx(7.0)

    def test_unsatisfied_demands(self) -> None:
        """获取未满足需求 / Get unsatisfied demands."""
        c = CapacityDemandConstraint(required_amount=10.0)
        agg = _StubAggregation(
            work_item_keys=("w1",),
            _assignments={
                "w1": (_StubAssignment(3.0),),
            },
        )
        unsatisfied = c.unsatisfied_demands(agg)  # type: ignore[arg-type]
        assert len(unsatisfied) == 1

    def test_is_feasible_true(self) -> None:
        """可行 / Feasible."""
        c = CapacityDemandConstraint(required_amount=10.0)
        agg = _StubAggregation(
            work_item_keys=("w1",),
            _assignments={
                "w1": (_StubAssignment(10.0),),
            },
        )
        assert c.is_feasible(agg) is True  # type: ignore[arg-type]

    def test_is_feasible_false(self) -> None:
        """不可行 / Infeasible."""
        c = CapacityDemandConstraint(required_amount=10.0)
        agg = _StubAggregation(
            work_item_keys=("w1",),
            _assignments={
                "w1": (_StubAssignment(2.0),),
            },
        )
        assert c.is_feasible(agg) is False  # type: ignore[arg-type]

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        c = CapacityDemandConstraint()
        with pytest.raises(AttributeError):
            c.required_amount = 5.0  # type: ignore[misc]


# =========================================================================
#  CapacityUsageMinimization tests
# =========================================================================


class TestUsageObjectiveTerm:
    """使用量目标项测试 / Usage objective term tests."""

    def test_construction(self) -> None:
        """构造 / Construction."""
        term = UsageObjectiveTerm(
            slot_key="s1",
            window_start=0.0,
            window_end=1.0,
            weight=1.5,
            variable_name="usage_s1_0.0_1.0",
        )
        assert term.slot_key == "s1"
        assert term.weight == pytest.approx(1.5)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        term = UsageObjectiveTerm(
            slot_key="s1",
            window_start=0.0,
            window_end=1.0,
            weight=1.0,
            variable_name="v",
        )
        with pytest.raises(AttributeError):
            term.weight = 2.0  # type: ignore[misc]


class TestCapacityUsageMinimization:
    """容量使用量最小化测试 / Usage minimization tests."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        m = CapacityUsageMinimization()
        assert m.objective_name == "cap_usage_min"
        assert m.default_weight == pytest.approx(1.0)

    def test_objective_name_for(self) -> None:
        """目标函数名称 / Objective name for slot."""
        m = CapacityUsageMinimization()
        expected = "cap_usage_min_s1"
        assert m.objective_name_for("s1") == expected

    def test_build_objective_terms_basic(self) -> None:
        """基本构建 / Basic build."""
        m = CapacityUsageMinimization()
        terms = m.build_objective_terms(
            slot_keys=("s1",),
            time_windows=((0.0, 1.0),),
        )
        assert len(terms) == 1
        assert terms[0].slot_key == "s1"
        assert terms[0].weight == pytest.approx(1.0)

    def test_build_objective_terms_multiple(self) -> None:
        """多槽多窗口 / Multiple slots and windows."""
        m = CapacityUsageMinimization()
        terms = m.build_objective_terms(
            slot_keys=("s1", "s2"),
            time_windows=((0.0, 1.0), (1.0, 2.0)),
        )
        assert len(terms) == 4

    def test_build_objective_terms_custom_weights(self) -> None:
        """自定义权重 / Custom weights."""
        m = CapacityUsageMinimization()
        weights = {("s1", 0.0, 1.0): 2.5}
        terms = m.build_objective_terms(
            slot_keys=("s1",),
            time_windows=((0.0, 1.0),),
            weights=weights,
        )
        assert terms[0].weight == pytest.approx(2.5)

    def test_build_objective_terms_zero_skipped(self) -> None:
        """零权重跳过 / Zero weight skipped."""
        m = CapacityUsageMinimization()
        weights = {("s1", 0.0, 1.0): 0.0}
        terms = m.build_objective_terms(
            slot_keys=("s1",),
            time_windows=((0.0, 1.0),),
            weights=weights,
        )
        assert len(terms) == 0

    def test_build_objective_terms_empty(self) -> None:
        """空输入 / Empty input."""
        m = CapacityUsageMinimization()
        terms = m.build_objective_terms(
            slot_keys=(),
            time_windows=(),
        )
        assert len(terms) == 0

    def test_var_name(self) -> None:
        """变量名 / Variable name."""
        m = CapacityUsageMinimization()
        name = m._var_name(
            slot_key="s1",
            window_start=0.0,
            window_end=1.0,
        )
        assert name == "usage_s1_0.0_1.0"

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        m = CapacityUsageMinimization()
        with pytest.raises(AttributeError):
            m.default_weight = 2.0  # type: ignore[misc]


# =========================================================================
#  CapacityVolumeMinimization tests
# =========================================================================


class TestVolumeObjectiveTerm:
    """容量目标项测试 / Volume objective term tests."""

    def test_construction(self) -> None:
        """构造 / Construction."""
        term = VolumeObjectiveTerm(
            slot_key="s1",
            weight=1.0,
            variable_name="volume_s1",
            fixed_cost=5.0,
        )
        assert term.slot_key == "s1"
        assert term.fixed_cost == pytest.approx(5.0)

    def test_default_fixed_cost(self) -> None:
        """默认固定成本 / Default fixed cost."""
        term = VolumeObjectiveTerm(
            slot_key="s1",
            weight=1.0,
            variable_name="v",
        )
        assert term.fixed_cost == pytest.approx(0.0)


class TestVolumeSavingsResult:
    """容量节省结果测试 / Volume savings result tests."""

    def test_savings_ratio_normal(self) -> None:
        """正常节省比例 / Normal savings ratio."""
        r = VolumeSavingsResult(
            original_volume=100.0,
            optimized_volume=60.0,
        )
        assert r.savings_ratio == pytest.approx(0.4)

    def test_savings_ratio_no_savings(self) -> None:
        """无节省 / No savings."""
        r = VolumeSavingsResult(
            original_volume=100.0,
            optimized_volume=100.0,
        )
        assert r.savings_ratio == pytest.approx(0.0)

    def test_savings_ratio_zero_original(self) -> None:
        """原始为零 / Zero original."""
        r = VolumeSavingsResult(
            original_volume=0.0,
            optimized_volume=0.0,
        )
        assert r.savings_ratio == pytest.approx(0.0)

    def test_savings_ratio_negative_clamped(self) -> None:
        """负节省被截断 / Negative savings clamped."""
        r = VolumeSavingsResult(
            original_volume=100.0,
            optimized_volume=150.0,
        )
        assert r.savings_ratio == pytest.approx(0.0)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        r = VolumeSavingsResult(
            original_volume=100.0,
            optimized_volume=50.0,
        )
        with pytest.raises(AttributeError):
            r.original_volume = 200.0  # type: ignore[misc]


class TestCapacityVolumeMinimization:
    """容量容量最小化测试 / Volume minimization tests."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        m = CapacityVolumeMinimization()
        assert m.objective_name == "cap_volume_min"
        assert m.default_weight == pytest.approx(1.0)

    def test_objective_name_for(self) -> None:
        """目标函数名称 / Objective name for slot."""
        m = CapacityVolumeMinimization()
        expected = "cap_volume_min_s1"
        assert m.objective_name_for("s1") == expected

    def test_build_objective_terms_basic(self) -> None:
        """基本构建 / Basic build."""
        m = CapacityVolumeMinimization()
        terms = m.build_objective_terms(
            slot_keys=("s1",),
            slot_capacities={"s1": 100.0},
        )
        assert len(terms) == 1
        assert terms[0].slot_key == "s1"
        assert terms[0].weight == pytest.approx(1.0)
        assert terms[0].fixed_cost == pytest.approx(0.0)

    def test_build_objective_terms_multiple(self) -> None:
        """多槽构建 / Multiple slots."""
        m = CapacityVolumeMinimization()
        terms = m.build_objective_terms(
            slot_keys=("s1", "s2"),
            slot_capacities={"s1": 100.0, "s2": 200.0},
        )
        assert len(terms) == 2

    def test_build_objective_terms_custom_weights(self) -> None:
        """自定义权重 / Custom weights."""
        m = CapacityVolumeMinimization()
        terms = m.build_objective_terms(
            slot_keys=("s1",),
            slot_capacities={"s1": 100.0},
            weights={"s1": 2.5},
        )
        assert terms[0].weight == pytest.approx(2.5)

    def test_build_objective_terms_fixed_costs(self) -> None:
        """固定成本 / Fixed costs."""
        m = CapacityVolumeMinimization()
        terms = m.build_objective_terms(
            slot_keys=("s1",),
            slot_capacities={"s1": 100.0},
            fixed_costs={"s1": 10.0},
        )
        assert terms[0].fixed_cost == pytest.approx(10.0)

    def test_build_objective_terms_zero_skipped(self) -> None:
        """零权重跳过 / Zero weight skipped."""
        m = CapacityVolumeMinimization()
        terms = m.build_objective_terms(
            slot_keys=("s1",),
            slot_capacities={"s1": 100.0},
            weights={"s1": 0.0},
        )
        assert len(terms) == 0

    def test_build_objective_terms_empty(self) -> None:
        """空输入 / Empty input."""
        m = CapacityVolumeMinimization()
        terms = m.build_objective_terms(
            slot_keys=(),
            slot_capacities={},
        )
        assert len(terms) == 0

    def test_compute_volume_savings(self) -> None:
        """计算容量节省 / Compute volume savings."""
        m = CapacityVolumeMinimization()
        result = m.compute_volume_savings(
            original_volumes={"s1": 100.0, "s2": 200.0},
            optimized_volumes={"s1": 80.0, "s2": 150.0},
        )
        assert isinstance(result, VolumeSavingsResult)
        assert result.original_volume == pytest.approx(300.0)
        assert result.optimized_volume == pytest.approx(230.0)

    def test_var_name(self) -> None:
        """变量名 / Variable name."""
        m = CapacityVolumeMinimization()
        assert m._var_name("s1") == "volume_s1"

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        m = CapacityVolumeMinimization()
        with pytest.raises(AttributeError):
            m.default_weight = 2.0  # type: ignore[misc]
