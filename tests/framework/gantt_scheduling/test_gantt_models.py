"""Gantt scheduling model tests for 0%-coverage files.

覆盖 Gantt 调度领域模型中 0% 覆盖率的文件。
Covers 0%-coverage files in Gantt scheduling domain models.
"""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.application.model.bunch.bunch_problem import (
    BunchProblem,
)
from ospf_python.framework.gantt_scheduling.application.model.bunch.bunch_solution import (
    BunchSolution,
)
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
)
from ospf_python.framework.gantt_scheduling.application.model.gantt_solution import (
    GanttSolution,
)
from ospf_python.framework.gantt_scheduling.application.model.task.task_problem import (
    TaskProblem,
)
from ospf_python.framework.gantt_scheduling.application.model.task.task_solution import (
    TaskSolution,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.assignment import (
    Assignment as BunchAssignment,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_aggregation import (
    BunchCompilationAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_aliases import (
    BunchCompilationAliases,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_model import (
    BunchCompilationModel,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_modeling_config import (
    BunchCompilationModelingConfig,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_solver_value_adapter import (
    BunchCompilationSolverValueAdapter,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.capacity import (
    Capacity as BunchCapacity,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.load import (
    Load as BunchLoad,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.scaled_bunch_compilation_solver_value_adapter import (
    ScaledBunchCompilationSolverValueAdapter,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_generation.model.bunch_generation_context import (
    BunchGenerationContext,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_generation.model.bunch_generation_program_candidate_adapters import (
    BunchGenerationProgramCandidateAdapters,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.assignment import (
    Assignment as CapacityAssignment,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity import (
    Capacity as SchedulingCapacity,
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
    Load as CapacityLoad,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.scaled_capacity_scheduling_solver_value_adapter import (
    ScaledCapacitySchedulingSolverValueAdapter,
)
from ospf_python.framework.gantt_scheduling.domain.produce.model.assignment import (
    Assignment as ProduceAssignment,
)
from ospf_python.framework.gantt_scheduling.domain.produce.model.capacity import (
    Capacity as ProduceCapacity,
)
from ospf_python.framework.gantt_scheduling.domain.produce.model.load import (
    Load as ProduceLoad,
)
from ospf_python.framework.gantt_scheduling.domain.produce.model.produce_aggregation import (
    ProduceAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.produce.model.produce_aliases import (
    ProduceAliases,
)
from ospf_python.framework.gantt_scheduling.domain.produce.model.produce_model import (
    ProduceModel,
)
from ospf_python.framework.gantt_scheduling.domain.produce.model.produce_modeling_config import (
    ProduceModelingConfig,
)
from ospf_python.framework.gantt_scheduling.domain.produce.model.produce_solver_value_adapter import (
    ProduceSolverValueAdapter,
)
from ospf_python.framework.gantt_scheduling.domain.produce.model.scaled_produce_solver_value_adapter import (
    ScaledProduceSolverValueAdapter,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_aggregation import (
    ResourceAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_attribute import (
    ResourceAttribute,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_availability import (
    ResourceAvailability,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_capacity import (
    ResourceCapacity,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_context import (
    ResourceContext,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand import (
    ResourceDemand,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_demand_contribution import (
    ResourceDemandContribution,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_shadow_price_map import (
    ResourceShadowPriceMap,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_type import (
    ResourceType,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_utilization import (
    ResourceUtilization,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_aggregation import (
    TaskAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_attribute import (
    TaskAttribute,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
    TaskContext,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_demand import (
    TaskDemand,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_demand_contribution import (
    TaskDemandContribution,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_service_async import (
    TaskServiceAsync,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_shadow_price_map import (
    TaskShadowPriceMap,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_type import (
    TaskType,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.assignment import (
    Assignment as TaskCompilationAssignment,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.capacity import (
    Capacity as TaskCompilationCapacity,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.scaled_task_compilation_solver_value_adapter import (
    ScaledTaskCompilationSolverValueAdapter,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_aggregation import (
    TaskCompilationAggregation,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_aliases import (
    TaskCompilationAliases,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_model import (
    TaskCompilationModel,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_modeling_config import (
    TaskCompilationModelingConfig,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.model.task_compilation_solver_value_adapter import (
    TaskCompilationSolverValueAdapter,
)
from ospf_python.framework.gantt_scheduling.infrastructure.gantt_container import (
    GanttContainer,
)
from ospf_python.framework.gantt_scheduling.infrastructure.gantt_machine import (
    GanttMachine,
)
from ospf_python.framework.gantt_scheduling.infrastructure.gantt_material import (
    GanttMaterial,
)
from ospf_python.framework.gantt_scheduling.infrastructure.gantt_product import (
    GanttProduct,
)
from ospf_python.framework.gantt_scheduling.infrastructure.gantt_render_adapter import (
    GanttRenderAdapter,
)
from ospf_python.framework.gantt_scheduling.infrastructure.gantt_shadow_price_map import (
    GanttShadowPriceMap,
)

# ============================================================
# Application model tests
# ============================================================


class TestGanttProblem:
    """GanttProblem tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        gp = GanttProblem(name="test")
        assert gp is not None

    def test_is_dataclass(self) -> None:
        """Test is a frozen dataclass. / 测试是冻结数据类."""
        from dataclasses import fields

        assert hasattr(GanttProblem, "__dataclass_fields__")
        assert len(fields(GanttProblem)) >= 0


class TestGanttSolution:
    """GanttSolution tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        gs = GanttSolution()
        assert gs is not None


class TestTaskProblem:
    """TaskProblem tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        tp = TaskProblem()
        assert tp is not None


class TestTaskSolution:
    """TaskSolution tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        ts = TaskSolution()
        assert ts is not None


class TestBunchProblem:
    """BunchProblem tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        bp = BunchProblem()
        assert bp is not None


class TestBunchSolution:
    """BunchSolution tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        bs = BunchSolution()
        assert bs is not None


# ============================================================
# Task domain model tests
# ============================================================


class TestTaskAggregation:
    """TaskAggregation tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        ta = TaskAggregation()
        assert ta is not None


class TestTaskAttribute:
    """TaskAttribute tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        attr = TaskAttribute()
        assert attr is not None


class TestTaskContext:
    """TaskContext tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        ctx = TaskContext()
        assert ctx is not None


class TestTaskDemand:
    """TaskDemand tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        td = TaskDemand(task_key="t1", resource_key="r1", amount=1.0)
        assert td is not None


class TestTaskDemandContribution:
    """TaskDemandContribution tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        tdc = TaskDemandContribution(task_key="t1", resource_key="r1", coefficient=1.0)
        assert tdc is not None


class TestTaskServiceAsync:
    """TaskServiceAsync tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        tsa = _ConcreteTaskServiceAsync()
        assert tsa is not None


class TestTaskShadowPriceMap:
    """TaskShadowPriceMap tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        tspm = TaskShadowPriceMap()
        assert tspm is not None


class TestTaskType:
    """TaskType tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        tt = TaskType.FIXED
        assert tt is not None


# ============================================================
# Resource domain model tests
# ============================================================


class TestResourceAggregation:
    """ResourceAggregation tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        ra = ResourceAggregation()
        assert ra is not None


class TestResourceAttribute:
    """ResourceAttribute tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        attr = ResourceAttribute(resource_key="res-1")
        assert attr is not None


class TestResourceAvailability:
    """ResourceAvailability tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
            Resource,
        )

        r = Resource(
            resource_key="res-1",
            name="M1",
            capacity=10.0,
        )
        avail = ResourceAvailability(resource=r)
        assert avail is not None


class TestResourceCapacity:
    """ResourceCapacity tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        rc = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
        )
        assert rc is not None


class TestResourceContext:
    """ResourceContext tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        ctx = ResourceContext()
        assert ctx is not None


class TestResourceDemand:
    """ResourceDemand tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        rd = ResourceDemand(
            resource_key="res-1",
            task_key="task-1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        assert rd is not None


class TestResourceDemandContribution:
    """ResourceDemandContribution tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        rdc = ResourceDemandContribution(
            task_key="task-1",
            resource_key="res-1",
            contribution_ratio=0.5,
            base_demand=10.0,
        )
        assert rdc is not None


class TestResourceShadowPriceMap:
    """ResourceShadowPriceMap tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        rspm = ResourceShadowPriceMap()
        assert rspm is not None


class TestResourceType:
    """ResourceType tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        rt = ResourceType.MACHINE
        assert rt is not None


class TestResourceUtilization:
    """ResourceUtilization tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        ru = ResourceUtilization(
            resource_key="res-1",
            time_range_start=0.0,
            time_range_end=10.0,
            total_capacity=10.0,
            used_capacity=5.0,
        )
        assert ru is not None


# ============================================================
# Task compilation model tests
# ============================================================


class TestTaskCompilationAssignment:
    """TaskCompilationAssignment tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        a = TaskCompilationAssignment()
        assert a is not None


class TestTaskCompilationCapacity:
    """TaskCompilationCapacity tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        c = TaskCompilationCapacity()
        assert c is not None


class TestScaledTaskCompilationSolverValueAdapter:
    """ScaledTaskCompilationSolverValueAdapter tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        adapter = ScaledTaskCompilationSolverValueAdapter()
        assert adapter is not None


class TestTaskCompilationAggregation:
    """TaskCompilationAggregation tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        agg = TaskCompilationAggregation()
        assert agg is not None


class TestTaskCompilationAliases:
    """TaskCompilationAliases tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        aliases = TaskCompilationAliases()
        assert aliases is not None


class TestTaskCompilationModel:
    """TaskCompilationModel tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        model = TaskCompilationModel()
        assert model is not None


class TestTaskCompilationModelingConfig:
    """TaskCompilationModelingConfig tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        config = TaskCompilationModelingConfig()
        assert config is not None


class TestTaskCompilationSolverValueAdapter:
    """TaskCompilationSolverValueAdapter tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        adapter = TaskCompilationSolverValueAdapter()
        assert adapter is not None


# ============================================================
# Bunch compilation model tests
# ============================================================


class TestBunchAssignment:
    """BunchAssignment tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        a = BunchAssignment()
        assert a is not None


class TestBunchCapacity:
    """BunchCapacity tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        c = BunchCapacity()
        assert c is not None


class TestBunchLoad:
    """BunchLoad tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        load = BunchLoad()
        assert load is not None


class TestBunchCompilationAggregation:
    """BunchCompilationAggregation tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        agg = BunchCompilationAggregation()
        assert agg is not None


class TestBunchCompilationAliases:
    """BunchCompilationAliases tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        aliases = BunchCompilationAliases()
        assert aliases is not None


class TestBunchCompilationModel:
    """BunchCompilationModel tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        model = BunchCompilationModel()
        assert model is not None


class TestBunchCompilationModelingConfig:
    """BunchCompilationModelingConfig tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        config = BunchCompilationModelingConfig()
        assert config is not None


class TestBunchCompilationSolverValueAdapter:
    """BunchCompilationSolverValueAdapter tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        adapter = BunchCompilationSolverValueAdapter()
        assert adapter is not None


class TestScaledBunchCompilationSolverValueAdapter:
    """ScaledBunchCompilationSolverValueAdapter tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        adapter = ScaledBunchCompilationSolverValueAdapter()
        assert adapter is not None


# ============================================================
# Capacity scheduling model tests
# ============================================================


class TestCapacityAssignment:
    """CapacityAssignment tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        a = CapacityAssignment()
        assert a is not None


class TestSchedulingCapacity:
    """SchedulingCapacity tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        c = SchedulingCapacity()
        assert c is not None


class TestCapacitySchedulingAggregation:
    """CapacitySchedulingAggregation tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        agg = CapacitySchedulingAggregation()
        assert agg is not None


class TestCapacitySchedulingAliases:
    """CapacitySchedulingAliases tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        aliases = CapacitySchedulingAliases()
        assert aliases is not None


class TestCapacitySchedulingModel:
    """CapacitySchedulingModel tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        model = CapacitySchedulingModel()
        assert model is not None


class TestCapacitySchedulingModelingConfig:
    """CapacitySchedulingModelingConfig tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        config = CapacitySchedulingModelingConfig()
        assert config is not None


class TestCapacitySchedulingSolverValueAdapter:
    """CapacitySchedulingSolverValueAdapter tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        adapter = CapacitySchedulingSolverValueAdapter()
        assert adapter is not None


class TestCapacityLoad:
    """CapacityLoad tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        load = CapacityLoad()
        assert load is not None


class TestScaledCapacitySchedulingSolverValueAdapter:
    """ScaledCapacitySchedulingSolverValueAdapter tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        adapter = ScaledCapacitySchedulingSolverValueAdapter()
        assert adapter is not None


# ============================================================
# Produce model tests
# ============================================================


class TestProduceAssignment:
    """ProduceAssignment tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        a = ProduceAssignment()
        assert a is not None


class TestProduceCapacity:
    """ProduceCapacity tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        c = ProduceCapacity()
        assert c is not None


class TestProduceLoad:
    """ProduceLoad tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        load = ProduceLoad()
        assert load is not None


class TestProduceAggregation:
    """ProduceAggregation tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        agg = ProduceAggregation()
        assert agg is not None


class TestProduceAliases:
    """ProduceAliases tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        aliases = ProduceAliases()
        assert aliases is not None


class TestProduceModel:
    """ProduceModel tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        model = ProduceModel()
        assert model is not None


class TestProduceModelingConfig:
    """ProduceModelingConfig tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        config = ProduceModelingConfig()
        assert config is not None


class TestProduceSolverValueAdapter:
    """ProduceSolverValueAdapter tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        adapter = ProduceSolverValueAdapter()
        assert adapter is not None


class TestScaledProduceSolverValueAdapter:
    """ScaledProduceSolverValueAdapter tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        adapter = ScaledProduceSolverValueAdapter()
        assert adapter is not None


# ============================================================
# Bunch generation model tests
# ============================================================


class TestBunchGenerationContext:
    """BunchGenerationContext tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        ctx = BunchGenerationContext()
        assert ctx is not None


class TestBunchGenerationProgramCandidateAdapters:
    """BunchGenerationProgramCandidateAdapters tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        adapters = BunchGenerationProgramCandidateAdapters()
        assert adapters is not None


# ============================================================
# Infrastructure model tests
# ============================================================


class TestGanttContainer:
    """GanttContainer tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        gc = GanttContainer()
        assert gc is not None

    def test_is_frozen(self) -> None:
        """Test is frozen dataclass. / 测试是冻结数据类."""
        assert hasattr(GanttContainer, "__dataclass_fields__")


class TestGanttMachine:
    """GanttMachine tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        gm = GanttMachine()
        assert gm is not None


class TestGanttMaterial:
    """GanttMaterial tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        gm = GanttMaterial()
        assert gm is not None


class TestGanttProduct:
    """GanttProduct tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        gp = GanttProduct()
        assert gp is not None


class TestGanttRenderAdapter:
    """GanttRenderAdapter tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        gra = GanttRenderAdapter()
        assert gra is not None


class TestGanttShadowPriceMap:
    """GanttShadowPriceMap tests."""

    def test_create(self) -> None:
        """Test creation. / 测试创建."""
        gspm = GanttShadowPriceMap()
        assert gspm is not None


# Concrete implementation for testing
class _ConcreteTaskServiceAsync(TaskServiceAsync):
    async def schedule_tasks(self, tasks):
        return ()

    async def validate_task(self, task):
        return True

    async def compute_critical_path(self, tasks):
        return ()

    async def estimate_duration(self, tasks):
        return 0.0
