"""Core solver module.

Provides solver abstraction and mock solver for testing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, unique
from typing import TypeVar

from ospf_python.core.model import MetaModel, Solution
from ospf_python.utils.error import ErrorCode
from ospf_python.utils.result import Failed, Result, failed, ok

V = TypeVar("V")


@unique
class SolverStatus(Enum):
    """Solver status.

    求解器状态。
    """

    OPTIMAL = "optimal"
    INFEASIBLE = "infeasible"
    UNBOUNDED = "unbounded"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SolverConfig:
    """Solver configuration.

    求解器配置。
    """

    time_limit: float = 3600.0
    gap_tolerance: float = 1e-4
    verbose: bool = False

    def __repr__(self) -> str:
        return f"SolverConfig(time_limit={self.time_limit}, gap_tolerance={self.gap_tolerance})"


@dataclass(frozen=True, slots=True)
class SolverOutput:
    """Solver output.

    求解器输出。
    """

    status: SolverStatus
    objective_value: float
    variable_values: dict[str, float]
    solve_time: float = 0.0

    def __repr__(self) -> str:
        return f"SolverOutput(status={self.status.value}, obj={self.objective_value})"


class Solver(ABC):
    """Solver interface.

    求解器接口。
    """

    @abstractmethod
    def solve(
        self, model: MetaModel, config: SolverConfig | None = None
    ) -> Result[SolverOutput]:
        """Solve the model.

        Args:
            model: Model to solve.
            config: Solver configuration.

        Returns:
            Result with solver output or error.
        """
        ...

    @abstractmethod
    def name(self) -> str:
        """Get solver name."""
        ...


class MockSolver(Solver):
    """Mock solver for testing.

    测试用 mock 求解器。
    """

    def __init__(self, solution: dict[str, float] | None = None) -> None:
        """Initialize mock solver.

        Args:
            solution: Pre-defined solution values.
        """
        self._solution = solution or {}

    def solve(
        self, model: MetaModel, config: SolverConfig | None = None
    ) -> Result[SolverOutput]:
        """Solve the model using mock values.

        Args:
            model: Model to solve.
            config: Solver configuration.

        Returns:
            Result with solver output.
        """
        # Get variables
        variables = model.get_variables()

        # Use provided solution or default values
        variable_values = {}
        for var in variables:
            if var.name in self._solution:
                variable_values[var.name] = self._solution[var.name]
            elif var.lower_bound is not None:
                variable_values[var.name] = var.lower_bound
            elif var.upper_bound is not None:
                variable_values[var.name] = var.upper_bound
            else:
                variable_values[var.name] = 0.0

        # Evaluate objective
        objective = model.get_objective()
        if objective is None:
            return failed(ErrorCode.ILLEGAL_STATE, "No objective set")

        objective_value = objective.expression.evaluate(variable_values)

        return ok(
            SolverOutput(
                status=SolverStatus.OPTIMAL,
                objective_value=objective_value,
                variable_values=variable_values,
                solve_time=0.001,
            )
        )

    def name(self) -> str:
        """Get solver name."""
        return "MockSolver"


def solve_with_mock(
    model: MetaModel, solution: dict[str, float] | None = None
) -> Result[Solution]:
    """Solve model with mock solver.

    Args:
        model: Model to solve.
        solution: Pre-defined solution values.

    Returns:
        Result with solution.
    """
    solver = MockSolver(solution)
    result = solver.solve(model)
    if isinstance(result, Failed):
        return failed(result.error)
    output = result.value  # type: ignore[union-attr]
    return ok(
        Solution(
            objective_value=output.objective_value,
            variable_values=output.variable_values,
            status=output.status.value,
        )
    )
