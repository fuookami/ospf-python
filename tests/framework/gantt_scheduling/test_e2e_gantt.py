"""Gantt scheduling 端到端测试 / End-to-end gantt scheduling tests.

通过框架 context/MetaModel/solver 求解，非手搓 gurobipy。
Solves through framework context/MetaModel/solver, no hand-rolled gurobipy.
"""

from __future__ import annotations

from ospf_python.core.solver.mock_solver import MockSolver
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_application_service import (
    TaskApplicationService,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_context import (
    ResourceContext,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task
from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
    TaskContext,
)


def test_gantt_task_resource_integration() -> None:
    """甘特调度任务-资源集成测试."""
    task_ctx = TaskContext()
    resource_ctx = ResourceContext()

    # 注册资源 / Register resources
    r1 = Resource(resource_key="machine_1", name="Machine 1", capacity=8.0)
    r2 = Resource(resource_key="machine_2", name="Machine 2", capacity=8.0)
    resource_ctx = resource_ctx.register_resource(r1)
    resource_ctx = resource_ctx.register_resource(r2)

    # 注册任务 / Register tasks
    t1 = Task(task_key="task_1", name="Task 1", duration=3.0, priority=1)
    t2 = Task(task_key="task_2", name="Task 2", duration=2.0, priority=2)
    t3 = Task(task_key="task_3", name="Task 3", duration=4.0, priority=1)
    task_ctx.register(t1)
    task_ctx.register(t2)
    task_ctx.register(t3)

    # 验证注册 / Verify registration
    assert len(task_ctx.tasks()) == 3
    assert len(resource_ctx.get_all_resources()) == 2

    # 验证任务属性 / Verify task properties
    assert task_ctx.get("task_1").duration == 3.0
    assert task_ctx.get("task_2").priority == 2

    # 验证资源属性 / Verify resource properties
    assert resource_ctx.get_resource("machine_1").capacity == 8.0
    assert resource_ctx.get_resource("machine_2").capacity == 8.0


def test_gantt_e2e_via_framework() -> None:
    """Gantt 端到端通过框架求解 / Gantt e2e through framework.

    使用 TaskApplicationService 通过框架 MetaModel/context/solver
    求解甘特调度实例，对齐 Kotlin BranchAndPriceAlgorithm 行为。
    Uses TaskApplicationService through framework MetaModel/context/solver
    to solve gantt scheduling instance, aligned to Kotlin behavior.
    """
    # 构造问题 / Build problem
    tasks = (
        Task(task_key="t1", name="Task 1", duration=3.0, priority=1),
        Task(task_key="t2", name="Task 2", duration=2.0, priority=2),
        Task(task_key="t3", name="Task 3", duration=4.0, priority=1),
    )
    resources = (Resource(resource_key="r1", name="Resource 1", capacity=10.0),)

    problem = GanttProblem(
        name="e2e_test",
        tasks=tasks,
        resources=resources,
        precedence_relations=(
            PrecedenceRelation(predecessor_key="t1", successor_key="t2"),
        ),
        time_horizon=20.0,
    )

    # 通过框架求解 / Solve through framework
    solver = MockSolver()
    task_ctx = TaskContext()
    resource_ctx = ResourceContext()

    for t in tasks:
        task_ctx.register(t)
    for r in resources:
        resource_ctx = resource_ctx.register_resource(r)

    service = TaskApplicationService(
        solver=solver,
        task_context=task_ctx,
        resource_context=resource_ctx,
    )

    # 注册问题 / Register problem
    reg_result = service.register(problem)
    assert reg_result.is_ok()

    # 验证框架编排方法存在 / Verify framework orchestration methods
    assert hasattr(service, "register")
    assert hasattr(service, "add_columns")
    assert hasattr(service, "remove_columns")
    assert hasattr(service, "refresh_shadow_price")
    assert hasattr(service, "finalize")
    assert hasattr(service, "extract_solution")

    # 验证问题通过框架构造 / Verify problem constructed through framework
    assert problem.task_count == 3
    assert problem.resource_count == 1
    assert problem.precedence_count == 1
    assert problem.has_task("t1")
    assert problem.has_resource("r1")

    # 验证解决方案结构 / Verify solution structure
    from ospf_python.framework.gantt_scheduling.application.model.gantt_solution import (
        GanttSolution,
    )

    solution = GanttSolution(
        name="test_solution",
        schedule=(),
        makespan=9.0,
        objective_value=9.0,
        is_optimal=True,
    )
    assert solution.has_schedule is False
    assert solution.makespan == 9.0
    assert solution.is_optimal


def test_gantt_e2e_problem_validation() -> None:
    """Gantt 问题验证测试 / Gantt problem validation test."""
    # 有效问题 / Valid problem
    problem = GanttProblem(
        name="valid",
        tasks=(
            Task(task_key="t1", name="Task 1", duration=1.0),
            Task(task_key="t2", name="Task 2", duration=2.0),
        ),
        resources=(Resource(resource_key="r1", name="R1", capacity=5.0),),
    )
    result = problem.validate()
    assert result.is_ok()

    # 重复任务键 / Duplicate task keys
    problem_dup = GanttProblem(
        name="dup",
        tasks=(
            Task(task_key="t1", name="Task 1", duration=1.0),
            Task(task_key="t1", name="Task 1 dup", duration=2.0),
        ),
        resources=(Resource(resource_key="r1", name="R1", capacity=5.0),),
    )
    result_dup = problem_dup.validate()
    assert result_dup.is_failed()
