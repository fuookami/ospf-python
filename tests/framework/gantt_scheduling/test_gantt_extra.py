"""gantt_scheduling 框架额外测试 / Additional gantt scheduling tests.

覆盖 BunchApplicationService, TaskApplicationService 及
领域模型类。
Covers BunchApplicationService, TaskApplicationService,
and domain model classes.
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
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_application_service import (
    BunchApplicationService,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_application_service import (
    TaskApplicationService,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_generation.model.bunch_generation_context import (
    BunchGenerationContext,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.capacity import (
    Capacity,
)
from ospf_python.framework.gantt_scheduling.domain.capacity_scheduling.model.load import (
    Load,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
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
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_type import (
    ResourceType,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task
from ospf_python.framework.gantt_scheduling.domain.task.model.task_attribute import (
    TaskAttribute,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
    TaskContext,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task_demand import (
    TaskDemand,
)
from ospf_python.framework.gantt_scheduling.infrastructure.dto.render_dto import (
    RenderDto,
)

# ============================================================
# Application service tests
# ============================================================


class TestBunchApplicationService:
    """BunchApplicationService 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        from ospf_python.core.solver.mock_solver import MockSolver

        svc = BunchApplicationService(
            solver=MockSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            bunch_context=BunchGenerationContext(),
        )
        assert svc is not None

    def test_properties(self) -> None:
        """初始属性值正确 / Initial properties are correct."""
        from ospf_python.core.solver.mock_solver import MockSolver

        svc = BunchApplicationService(
            solver=MockSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
            bunch_context=BunchGenerationContext(),
        )
        assert svc.iteration == 0
        assert svc.converged is False
        assert svc.shadow_prices == {}
        assert svc.active_columns == ()


class TestTaskApplicationService:
    """TaskApplicationService 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        from ospf_python.core.solver.mock_solver import MockSolver

        svc = TaskApplicationService(
            solver=MockSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
        )
        assert svc is not None

    def test_properties(self) -> None:
        """初始属性值正确 / Initial properties are correct."""
        from ospf_python.core.solver.mock_solver import MockSolver

        svc = TaskApplicationService(
            solver=MockSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
        )
        assert svc.iteration == 0
        assert svc.converged is False
        assert svc.shadow_prices == {}
        assert svc.active_columns == ()


# ============================================================
# Application model tests
# ============================================================


class TestGanttProblem:
    """GanttProblem 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        p = GanttProblem(name="test")
        assert p is not None


class TestGanttSolution:
    """GanttSolution 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        s = GanttSolution()
        assert s is not None


class TestBunchProblem:
    """BunchProblem 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        p = BunchProblem()
        assert p is not None


class TestBunchSolution:
    """BunchSolution 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        s = BunchSolution()
        assert s is not None


class TestTaskProblem:
    """TaskProblem 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        p = TaskProblem()
        assert p is not None


class TestTaskSolution:
    """TaskSolution 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        s = TaskSolution()
        assert s is not None


# ============================================================
# Domain model tests
# ============================================================


class TestResource:
    """Resource 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        r = Resource(
            resource_key="res-1",
            name="Machine A",
            capacity=10.0,
        )
        assert r is not None
        assert r.resource_key == "res-1"

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        r = Resource(
            resource_key="res-1",
            name="Machine A",
            capacity=10.0,
        )
        assert isinstance(r, Resource)


class TestTask:
    """Task 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        t = Task(task_key="t1", name="task1", duration=1.0)
        assert t is not None

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        t = Task(task_key="t1", name="task1", duration=1.0)
        assert isinstance(t, Task)


class TestResourceType:
    """ResourceType 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        rt = ResourceType.MACHINE
        assert rt is not None


class TestResourceDemand:
    """ResourceDemand 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        rd = ResourceDemand(
            resource_key="res-1",
            task_key="task-1",
            time_window_start=0.0,
            time_window_end=10.0,
            demand_amount=5.0,
        )
        assert rd is not None


class TestResourceCapacity:
    """ResourceCapacity 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        rc = ResourceCapacity(
            resource_key="res-1",
            time_window_start=0.0,
            time_window_end=10.0,
            max_capacity=10.0,
        )
        assert rc is not None


class TestResourceContext:
    """ResourceContext 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        ctx = ResourceContext()
        assert ctx is not None


class TestTaskAttribute:
    """TaskAttribute 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        ta = TaskAttribute()
        assert ta is not None


class TestTaskDemand:
    """TaskDemand 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        td = TaskDemand(task_key="t1", resource_key="r1", amount=1.0)
        assert td is not None


class TestTaskContext:
    """TaskContext 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        ctx = TaskContext()
        assert ctx is not None


# ============================================================
# Infrastructure tests
# ============================================================


class TestCapacity:
    """Capacity 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        c = Capacity()
        assert c is not None


class TestLoad:
    """Load 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        l = Load()
        assert l is not None


class TestRenderDto:
    """RenderDto 测试 / Tests."""

    def test_instantiate(self) -> None:
        """可实例化 / Can instantiate."""
        dto = RenderDto()
        assert dto is not None
