"""生产限制测试 / Produce limits tests.

覆盖 produce.service.limits 中所有约束和目标类的桩方法。
Covers all stub constraint and objective classes in
produce.service.limits.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_batch_capacity_constraint import (
    ProduceBatchCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_batch_demand_constraint import (
    ProduceBatchDemandConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_batch_maximization import (
    ProduceBatchMaximization,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_batch_minimization import (
    ProduceBatchMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_batch_order_constraint import (
    ProduceBatchOrderConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_capacity_constraint import (
    ProduceCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_demand_constraint import (
    ProduceDemandConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_order_constraint import (
    ProduceOrderConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_usage_minimization import (
    ProduceUsageMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_volume_minimization import (
    ProduceVolumeMinimization,
)

# =========================================================================
#  Constraint classes tests
# =========================================================================


class TestProduceBatchCapacityConstraint:
    """批次容量约束测试 / Batch capacity constraint tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        c = ProduceBatchCapacityConstraint()
        assert c.name == "produce batch capacity constraint"

    def test_build_constraints_returns_empty(self) -> None:
        """构建约束返回空 / Build constraints returns empty."""
        c = ProduceBatchCapacityConstraint()
        assert c.build_constraints(None, None) == ()

    def test_is_satisfied(self) -> None:
        """满足约束 / Constraint satisfied."""
        c = ProduceBatchCapacityConstraint()
        assert c.is_satisfied(None) is True

    def test_violations_empty(self) -> None:
        """无违反 / No violations."""
        c = ProduceBatchCapacityConstraint()
        assert c.violations(None) == ()

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        c = ProduceBatchCapacityConstraint()
        with pytest.raises(AttributeError):
            c.name = "x"  # type: ignore[misc]


class TestProduceBatchDemandConstraint:
    """批次需求约束测试 / Batch demand constraint tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        c = ProduceBatchDemandConstraint()
        assert c.name == "produce batch demand constraint"

    def test_build_constraints_returns_empty(self) -> None:
        """构建约束返回空 / Build constraints returns empty."""
        c = ProduceBatchDemandConstraint()
        assert c.build_constraints(None, None) == ()

    def test_is_satisfied(self) -> None:
        """满足约束 / Constraint satisfied."""
        c = ProduceBatchDemandConstraint()
        assert c.is_satisfied(None) is True

    def test_violations_empty(self) -> None:
        """无违反 / No violations."""
        c = ProduceBatchDemandConstraint()
        assert c.violations(None) == ()

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        c = ProduceBatchDemandConstraint()
        with pytest.raises(AttributeError):
            c.name = "x"  # type: ignore[misc]


class TestProduceBatchOrderConstraint:
    """批次排序约束测试 / Batch order constraint tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        c = ProduceBatchOrderConstraint()
        assert c.name == "produce batch order constraint"

    def test_build_constraints_returns_empty(self) -> None:
        """构建约束返回空 / Build constraints returns empty."""
        c = ProduceBatchOrderConstraint()
        assert c.build_constraints(None, None) == ()

    def test_is_satisfied(self) -> None:
        """满足约束 / Constraint satisfied."""
        c = ProduceBatchOrderConstraint()
        assert c.is_satisfied(None) is True

    def test_violations_empty(self) -> None:
        """无违反 / No violations."""
        c = ProduceBatchOrderConstraint()
        assert c.violations(None) == ()

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        c = ProduceBatchOrderConstraint()
        with pytest.raises(AttributeError):
            c.name = "x"  # type: ignore[misc]


class TestProduceCapacityConstraint:
    """容量约束测试 / Capacity constraint tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        c = ProduceCapacityConstraint()
        assert c.name == "produce capacity constraint"

    def test_build_constraints_returns_empty(self) -> None:
        """构建约束返回空 / Build constraints returns empty."""
        c = ProduceCapacityConstraint()
        assert c.build_constraints(None, None) == ()

    def test_is_satisfied(self) -> None:
        """满足约束 / Constraint satisfied."""
        c = ProduceCapacityConstraint()
        assert c.is_satisfied(None) is True

    def test_violations_empty(self) -> None:
        """无违反 / No violations."""
        c = ProduceCapacityConstraint()
        assert c.violations(None) == ()

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        c = ProduceCapacityConstraint()
        with pytest.raises(AttributeError):
            c.name = "x"  # type: ignore[misc]


class TestProduceDemandConstraint:
    """需求约束测试 / Demand constraint tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        c = ProduceDemandConstraint()
        assert c.name == "produce demand constraint"

    def test_build_constraints_returns_empty(self) -> None:
        """构建约束返回空 / Build constraints returns empty."""
        c = ProduceDemandConstraint()
        assert c.build_constraints(None, None) == ()

    def test_is_satisfied(self) -> None:
        """满足约束 / Constraint satisfied."""
        c = ProduceDemandConstraint()
        assert c.is_satisfied(None) is True

    def test_violations_empty(self) -> None:
        """无违反 / No violations."""
        c = ProduceDemandConstraint()
        assert c.violations(None) == ()

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        c = ProduceDemandConstraint()
        with pytest.raises(AttributeError):
            c.name = "x"  # type: ignore[misc]


class TestProduceOrderConstraint:
    """排序约束测试 / Order constraint tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        c = ProduceOrderConstraint()
        assert c.name == "produce order constraint"

    def test_build_constraints_returns_empty(self) -> None:
        """构建约束返回空 / Build constraints returns empty."""
        c = ProduceOrderConstraint()
        assert c.build_constraints(None, None) == ()

    def test_is_satisfied(self) -> None:
        """满足约束 / Constraint satisfied."""
        c = ProduceOrderConstraint()
        assert c.is_satisfied(None) is True

    def test_violations_empty(self) -> None:
        """无违反 / No violations."""
        c = ProduceOrderConstraint()
        assert c.violations(None) == ()

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        c = ProduceOrderConstraint()
        with pytest.raises(AttributeError):
            c.name = "x"  # type: ignore[misc]


# =========================================================================
#  Objective classes tests
# =========================================================================


class TestProduceBatchMaximization:
    """批次最大化测试 / Batch maximization tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        o = ProduceBatchMaximization()
        assert o.name == "produce batch maximization"

    def test_build_objective_terms_returns_empty(self) -> None:
        """构建目标项返回空 / Build terms returns empty."""
        o = ProduceBatchMaximization()
        assert o.build_objective_terms(None, None) == ()

    def test_compute_value(self) -> None:
        """计算目标值 / Compute value."""
        o = ProduceBatchMaximization()
        assert o.compute_value(None) == pytest.approx(0.0)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        o = ProduceBatchMaximization()
        with pytest.raises(AttributeError):
            o.name = "x"  # type: ignore[misc]


class TestProduceBatchMinimization:
    """批次最小化测试 / Batch minimization tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        o = ProduceBatchMinimization()
        assert o.name == "produce batch minimization"

    def test_build_objective_terms_returns_empty(self) -> None:
        """构建目标项返回空 / Build terms returns empty."""
        o = ProduceBatchMinimization()
        assert o.build_objective_terms(None, None) == ()

    def test_compute_value(self) -> None:
        """计算目标值 / Compute value."""
        o = ProduceBatchMinimization()
        assert o.compute_value(None) == pytest.approx(0.0)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        o = ProduceBatchMinimization()
        with pytest.raises(AttributeError):
            o.name = "x"  # type: ignore[misc]


class TestProduceUsageMinimization:
    """使用量最小化测试 / Usage minimization tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        o = ProduceUsageMinimization()
        assert o.name == "produce usage minimization"

    def test_build_objective_terms_returns_empty(self) -> None:
        """构建目标项返回空 / Build terms returns empty."""
        o = ProduceUsageMinimization()
        assert o.build_objective_terms(None, None) == ()

    def test_compute_value(self) -> None:
        """计算目标值 / Compute value."""
        o = ProduceUsageMinimization()
        assert o.compute_value(None) == pytest.approx(0.0)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        o = ProduceUsageMinimization()
        with pytest.raises(AttributeError):
            o.name = "x"  # type: ignore[misc]


class TestProduceVolumeMinimization:
    """容量最小化测试 / Volume minimization tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        o = ProduceVolumeMinimization()
        assert o.name == "produce volume minimization"

    def test_build_objective_terms_returns_empty(self) -> None:
        """构建目标项返回空 / Build terms returns empty."""
        o = ProduceVolumeMinimization()
        assert o.build_objective_terms(None, None) == ()

    def test_compute_value(self) -> None:
        """计算目标值 / Compute value."""
        o = ProduceVolumeMinimization()
        assert o.compute_value(None) == pytest.approx(0.0)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        o = ProduceVolumeMinimization()
        with pytest.raises(AttributeError):
            o.name = "x"  # type: ignore[misc]
