"""Resource limits tests."""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.resource.service.limits.resource_capacity_constraint import (
    ResourceCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.resource.service.limits.resource_demand_constraint import (
    ResourceDemandConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.resource.service.limits.resource_usage_minimization import (
    ResourceUsageMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.resource.service.limits.resource_volume_minimization import (
    ResourceVolumeMinimization,
)


def test_resource_capacity_constraint() -> None:
    c = ResourceCapacityConstraint()
    assert c is not None


def test_resource_demand_constraint() -> None:
    c = ResourceDemandConstraint()
    assert c is not None


def test_resource_usage_minimization() -> None:
    o = ResourceUsageMinimization()
    assert o is not None


def test_resource_volume_minimization() -> None:
    o = ResourceVolumeMinimization()
    assert o is not None
