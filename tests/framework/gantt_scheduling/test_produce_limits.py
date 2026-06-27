"""Produce limits tests."""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_batch_capacity_constraint import (
    ProduceBatchCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_batch_demand_constraint import (
    ProduceBatchDemandConstraint,
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


class TestProduceBatchCapacityConstraint:
    def test_has_build_constraints(self) -> None:
        c = ProduceBatchCapacityConstraint()
        assert hasattr(c, "build_constraints")

    def test_has_is_satisfied(self) -> None:
        c = ProduceBatchCapacityConstraint()
        assert hasattr(c, "is_satisfied")

    def test_has_violations(self) -> None:
        c = ProduceBatchCapacityConstraint()
        assert hasattr(c, "violations")

    def test_constraint_name(self) -> None:
        c = ProduceBatchCapacityConstraint()
        name = c.constraint_name("batch1")
        assert isinstance(name, str)


class TestProduceBatchDemandConstraint:
    def test_has_build_constraints(self) -> None:
        c = ProduceBatchDemandConstraint()
        assert hasattr(c, "build_constraints")


class TestProduceBatchOrderConstraint:
    def test_has_build_constraints(self) -> None:
        c = ProduceBatchOrderConstraint()
        assert hasattr(c, "build_constraints")


class TestProduceCapacityConstraint:
    def test_has_build_constraints(self) -> None:
        c = ProduceCapacityConstraint()
        assert hasattr(c, "build_constraints")


class TestProduceDemandConstraint:
    def test_has_build_constraints(self) -> None:
        c = ProduceDemandConstraint()
        assert hasattr(c, "build_constraints")


class TestProduceOrderConstraint:
    def test_has_build_constraints(self) -> None:
        c = ProduceOrderConstraint()
        assert hasattr(c, "build_constraints")


class TestProduceUsageMinimization:
    def test_has_build_objective_terms(self) -> None:
        m = ProduceUsageMinimization()
        assert hasattr(m, "build_objective_terms")


class TestProduceVolumeMinimization:
    def test_has_build_objective_terms(self) -> None:
        m = ProduceVolumeMinimization()
        assert hasattr(m, "build_objective_terms")
