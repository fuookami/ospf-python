"""Gantt Scheduling framework.

Provides domain-specific framework for Gantt scheduling problems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from ospf_python.core.model import ConstraintType, MetaModel, ObjectiveType, Solution
from ospf_python.core.solver import MockSolver, Solver
from ospf_python.core.symbol import LinearExpression, LinearTerm
from ospf_python.core.variable import continuous, integer
from ospf_python.framework import FrameworkConfig, FrameworkModel, SimpleFrameworkSolver
from ospf_python.utils.result import Ok  # noqa: F401

if TYPE_CHECKING:
    from ospf_python.utils.result import Result

V = TypeVar("V")


@dataclass(frozen=True, slots=True)
class Task:
    """Task to be scheduled.

    待调度任务。
    """

    name: str
    duration: float
    priority: int = 0


@dataclass(frozen=True, slots=True)
class Resource:
    """Resource for scheduling.

    调度资源。
    """

    name: str
    capacity: int


@dataclass(frozen=True, slots=True)
class ScheduleEntry:
    """Schedule entry.

    调度条目。
    """

    task_name: str
    resource_name: str
    start_time: float
    end_time: float


@dataclass(frozen=True, slots=True)
class GanttSolution:
    """Gantt scheduling solution.

    甘特调度解决方案。
    """

    entries: list[ScheduleEntry]
    makespan: float
    total_idle_time: float
    objective_value: float


class GanttModel(FrameworkModel):
    """Gantt scheduling model.

    甘特调度模型。
    """

    def __init__(
        self,
        tasks: list[Task],
        resources: list[Resource],
        extra_constraints: list[object] | None = None,
    ) -> None:
        """Initialize.

        Args:
            tasks: Tasks to schedule.
            resources: Available resources.
            extra_constraints: Extra constraints for extension point.
        """
        self._tasks = tasks
        self._resources = resources
        self._extra_constraints = extra_constraints or []

    def build_meta_model(self) -> MetaModel:
        """Build the MetaModel."""
        model = MetaModel("gantt")

        # Add variables: start_time[i] = start time of task i
        for i, _task in enumerate(self._tasks):
            model.add_variable(continuous(f"start_{i}", 0.0))

        # Add variables: x[i][j] = 1 if task i is assigned to resource j
        for i, _task in enumerate(self._tasks):
            for j, _resource in enumerate(self._resources):
                model.add_variable(integer(f"x_{i}_{j}", 0, 1))

        # Add variable: makespan
        model.add_variable(continuous("makespan", 0.0))

        # Set objective: minimize makespan
        model.set_objective(
            "min_makespan",
            LinearTerm(1.0, "makespan"),
            ObjectiveType.MINIMIZE,
        )

        # Add constraints: each task assigned to exactly one resource
        for i, _task in enumerate(self._tasks):
            terms = []
            for j, _resource in enumerate(self._resources):
                terms.append(LinearTerm(1.0, f"x_{i}_{j}"))
            expr = LinearExpression(tuple(terms))
            model.add_constraint(f"task_{i}_assigned", expr, ConstraintType.EQ, 1.0)

        # Add constraints: makespan >= end time of each task
        for i, _task in enumerate(self._tasks):
            # makespan >= start_time[i] + duration[i]
            terms = [
                LinearTerm(1.0, "makespan"),
                LinearTerm(-1.0, f"start_{i}"),
            ]
            expr = LinearExpression(tuple(terms))
            model.add_constraint(
                f"makespan_{i}",
                expr,
                ConstraintType.GE,
                self._tasks[i].duration,
            )

        return model

    def extract_solution(self, solution: Solution) -> GanttSolution:
        """Extract domain solution from solver solution."""
        entries = []

        for i, _task in enumerate(self._tasks):
            start_time = solution.variable_values.get(f"start_{i}", 0.0)

            # Find assigned resource
            resource_name = self._resources[0].name if self._resources else "unknown"
            for j, resource in enumerate(self._resources):
                var_name = f"x_{i}_{j}"
                if solution.variable_values.get(var_name, 0) > 0.5:
                    resource_name = resource.name
                    break

            entries.append(
                ScheduleEntry(
                    task_name=self._tasks[i].name,
                    resource_name=resource_name,
                    start_time=start_time,
                    end_time=start_time + self._tasks[i].duration,
                )
            )

        makespan = solution.variable_values.get("makespan", 0.0)
        total_idle_time = 0.0  # Simplified calculation

        return GanttSolution(
            entries=entries,
            makespan=makespan,
            total_idle_time=total_idle_time,
            objective_value=solution.objective_value,
        )


class GanttSolver:
    """Gantt scheduling solver.

    甘特调度求解器。
    """

    def __init__(self, solver: Solver | None = None) -> None:
        """Initialize.

        Args:
            solver: Core solver (defaults to MockSolver).
        """
        self._solver = solver or MockSolver()
        self._framework_solver = SimpleFrameworkSolver(self._solver)

    def solve(
        self,
        tasks: list[Task],
        resources: list[Resource],
        config: FrameworkConfig | None = None,
        extra_constraints: list[object] | None = None,
    ) -> Result[GanttSolution]:
        """Solve Gantt scheduling problem.

        Args:
            tasks: Tasks to schedule.
            resources: Available resources.
            config: Framework configuration.
            extra_constraints: Extra constraints for extension point.

        Returns:
            Result with scheduling solution.
        """
        model = GanttModel(tasks, resources, extra_constraints)
        return self._framework_solver.solve(model, config)
