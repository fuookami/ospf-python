"""Task compilation limits tests."""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.batch_capacity_constraint import (
    BatchCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.batch_demand_constraint import (
    BatchDemandConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.batch_maximization import (
    BatchMaximization,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.batch_minimization import (
    BatchMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.batch_order_constraint import (
    BatchOrderConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.batch_volume_minimization import (
    BatchVolumeMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.better_task_maximization import (
    BetterTaskMaximization,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.precedence_constraint import (
    PrecedenceConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.resource_capacity_constraint import (
    ResourceCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.resource_demand_constraint import (
    ResourceDemandConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.resource_usage_minimization import (
    ResourceUsageMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.resource_volume_minimization import (
    ResourceVolumeMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.sequence_dependent_setup_constraint import (
    SequenceDependentSetupConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.setup_time_constraint import (
    SetupTimeConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.task_amount_minimization import (
    TaskAmountMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.task_capacity_constraint import (
    TaskCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.task_compilation_order_constraint import (
    TaskCompilationOrderConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.task_demand_constraint import (
    TaskDemandConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.task_rest_amount_minimization import (
    TaskRestAmountMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.task_tail_assignment_constraint import (
    TaskTailAssignmentConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.task_tail_loading_rate_minimization import (
    TaskTailLoadingRateMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.task_volume_minimization import (
    TaskVolumeMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.time_capacity_constraint import (
    TimeCapacityConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.time_demand_constraint import (
    TimeDemandConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.time_order_constraint import (
    TimeOrderConstraint,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.time_usage_minimization import (
    TimeUsageMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.time_volume_minimization import (
    TimeVolumeMinimization,
)


def test_batch_capacity_constraint() -> None:
    assert BatchCapacityConstraint() is not None


def test_batch_demand_constraint() -> None:
    assert BatchDemandConstraint() is not None


def test_batch_maximization() -> None:
    assert BatchMaximization() is not None


def test_batch_minimization() -> None:
    assert BatchMinimization() is not None


def test_batch_order_constraint() -> None:
    assert BatchOrderConstraint() is not None


def test_batch_volume_minimization() -> None:
    assert BatchVolumeMinimization() is not None


def test_better_task_maximization() -> None:
    assert BetterTaskMaximization() is not None


def test_precedence_constraint() -> None:
    assert PrecedenceConstraint() is not None


def test_resource_capacity_constraint() -> None:
    assert ResourceCapacityConstraint() is not None


def test_resource_demand_constraint() -> None:
    assert ResourceDemandConstraint() is not None


def test_resource_usage_minimization() -> None:
    assert ResourceUsageMinimization() is not None


def test_resource_volume_minimization() -> None:
    assert ResourceVolumeMinimization() is not None


def test_sequence_dependent_setup_constraint() -> None:
    assert SequenceDependentSetupConstraint() is not None


def test_setup_time_constraint() -> None:
    assert SetupTimeConstraint() is not None


def test_task_amount_minimization() -> None:
    assert TaskAmountMinimization() is not None


def test_task_capacity_constraint() -> None:
    assert TaskCapacityConstraint() is not None


def test_task_compilation_order_constraint() -> None:
    assert TaskCompilationOrderConstraint() is not None


def test_task_demand_constraint() -> None:
    assert TaskDemandConstraint() is not None


def test_task_rest_amount_minimization() -> None:
    assert TaskRestAmountMinimization() is not None


def test_task_tail_assignment_constraint() -> None:
    assert TaskTailAssignmentConstraint() is not None


def test_task_tail_loading_rate_minimization() -> None:
    assert TaskTailLoadingRateMinimization() is not None


def test_task_volume_minimization() -> None:
    assert TaskVolumeMinimization() is not None


def test_time_capacity_constraint() -> None:
    assert TimeCapacityConstraint() is not None


def test_time_demand_constraint() -> None:
    assert TimeDemandConstraint() is not None


def test_time_order_constraint() -> None:
    assert TimeOrderConstraint() is not None


def test_time_usage_minimization() -> None:
    assert TimeUsageMinimization() is not None


def test_time_volume_minimization() -> None:
    assert TimeVolumeMinimization() is not None
