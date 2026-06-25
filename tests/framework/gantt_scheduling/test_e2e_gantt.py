"""Gantt scheduling 端到端测试 / End-to-end gantt scheduling tests."""

from __future__ import annotations

import pytest

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


def test_gantt_scheduling_with_mock_solver() -> None:
    """使用 MockSolver 的甘特调度测试."""
    from ospf_python.core.solver.mock_solver import MockSolver

    solver = MockSolver()
    assert solver is not None
    assert solver.name == "mock"


def test_gantt_e2e_gurobi() -> None:
    """Gurobi 端到端甘特调度."""
    pytest.importorskip("gurobipy")
    import gurobipy as gp

    m = gp.Model("gantt_e2e")
    m.setParam("OutputFlag", 0)

    tasks = [
        {"key": "t1", "duration": 3, "priority": 1},
        {"key": "t2", "duration": 2, "priority": 2},
        {"key": "t3", "duration": 4, "priority": 1},
    ]

    start = {}
    for t in tasks:
        start[t["key"]] = m.addVar(name=f"start_{t['key']}", vtype="C", lb=0)

    makespan = m.addVar(name="makespan", vtype="C", lb=0)

    for t in tasks:
        m.addConstr(
            makespan >= start[t["key"]] + t["duration"],
            name=f"makespan_{t['key']}",
        )

    m.addConstr(start["t2"] >= start["t1"] + tasks[0]["duration"])

    m.setObjective(makespan, gp.GRB.MINIMIZE)
    m.optimize()

    assert m.status == gp.GRB.OPTIMAL
    assert makespan.X >= 5.0
    print(f"Gantt e2e: optimal makespan = {makespan.X:.1f}")

    schedule = {t["key"]: start[t["key"]].X for t in tasks}
    print(f"Schedule: {schedule}")

    m.dispose()


def test_gantt_e2e_scip() -> None:
    """SCIP 端到端甘特调度."""
    pytest.importorskip("pyscipopt")
    from pyscipopt import Model

    m = Model("gantt_e2e")

    tasks = [
        {"key": "t1", "duration": 3, "priority": 1},
        {"key": "t2", "duration": 2, "priority": 2},
        {"key": "t3", "duration": 4, "priority": 1},
    ]

    start = {}
    for t in tasks:
        start[t["key"]] = m.addVar(name=f"start_{t['key']}", vtype="CONTINUOUS", lb=0)

    makespan = m.addVar(name="makespan", vtype="CONTINUOUS", lb=0)

    for t in tasks:
        m.addCons(
            makespan >= start[t["key"]] + t["duration"],
            name=f"makespan_{t['key']}",
        )

    m.addCons(start["t2"] >= start["t1"] + tasks[0]["duration"])

    m.setObjective(makespan, "minimize")
    m.optimize()

    assert m.getStatus() == "optimal"
    sol = m.getBestSol()
    assert sol[makespan] >= 5.0
    print(f"Gantt e2e SCIP: optimal makespan = {sol[makespan]:.1f}")

    schedule = {t["key"]: sol[start[t["key"]]] for t in tasks}
    print(f"Schedule: {schedule}")
