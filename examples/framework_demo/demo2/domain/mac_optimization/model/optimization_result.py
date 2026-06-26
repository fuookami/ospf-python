"""优化结果 / Optimization result.

定义 MAC/CG 优化求解结果的数据结构。
Defines the data structure for MAC/CG optimization
solver results.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizationResult:
    """优化结果 / Optimization result.

    描述优化求解的最终状态，包括目标函数值、
    决策变量解和迭代次数。
    Describes the final state of an optimization solve,
    including the objective value, decision variable
    solution, and iteration count.

    Attributes:
        status: 求解状态 / Solver status.
        objective_value: 目标函数值 / Objective function value.
        solution: 决策变量解字典(变量名->值) /
            Decision variable solution dict (name -> value).
        iterations: 迭代次数 / Iteration count.
    """

    status: str
    """求解状态 (optimal/infeasible/unbounded/unknown) /
    Solver status (optimal/infeasible/unbounded/unknown)."""

    objective_value: float
    """目标函数值 / Objective function value."""

    solution: dict[str, float]
    """决策变量解字典 (变量名->值) /
    Decision variable solution dict (name -> value)."""

    iterations: int
    """迭代次数 / Iteration count."""

    @staticmethod
    def create_optimal(
        *,
        objective_value: float,
        solution: dict[str, float],
        iterations: int,
    ) -> OptimizationResult:
        """创建最优解结果 / Create optimal result.

        Args:
            objective_value: 目标函数值 / Objective value.
            solution: 决策变量解 / Decision variable solution.
            iterations: 迭代次数 / Iteration count.

        Returns:
            最优解结果 / Optimal result.
        """
        return OptimizationResult(
            status="optimal",
            objective_value=objective_value,
            solution=solution,
            iterations=iterations,
        )

    @staticmethod
    def create_infeasible(*, iterations: int) -> OptimizationResult:
        """创建不可行结果 / Create infeasible result.

        Args:
            iterations: 迭代次数 / Iteration count.

        Returns:
            不可行结果 / Infeasible result.
        """
        return OptimizationResult(
            status="infeasible",
            objective_value=0.0,
            solution={},
            iterations=iterations,
        )

    @staticmethod
    def create_unbounded(*, iterations: int) -> OptimizationResult:
        """创建无界结果 / Create unbounded result.

        Args:
            iterations: 迭代次数 / Iteration count.

        Returns:
            无界结果 / Unbounded result.
        """
        return OptimizationResult(
            status="unbounded",
            objective_value=float("inf"),
            solution={},
            iterations=iterations,
        )

    @staticmethod
    def create_unknown(
        *,
        iterations: int,
        objective_value: float = 0.0,
    ) -> OptimizationResult:
        """创建未知状态结果 / Create unknown status result.

        Args:
            iterations: 迭代次数 / Iteration count.
            objective_value: 目标函数值 / Objective value.

        Returns:
            未知状态结果 / Unknown status result.
        """
        return OptimizationResult(
            status="unknown",
            objective_value=objective_value,
            solution={},
            iterations=iterations,
        )

    @property
    def is_optimal(self) -> bool:
        """是否为最优解 / Whether optimal.

        Returns:
            状态为 optimal 则返回 True。
            True if status is optimal.
        """
        return self.status == "optimal"

    @property
    def is_feasible(self) -> bool:
        """是否可行 / Whether feasible.

        最优解和未知状态（可能可行）均视为可行。
        Both optimal and unknown (potentially feasible)
        are considered feasible.

        Returns:
            可行时返回 True / True if feasible.
        """
        return self.status in ("optimal", "unknown")

    def variable_value(self, name: str) -> float | None:
        """获取指定变量的解值 / Get solution value for variable.

        Args:
            name: 变量名 / Variable name.

        Returns:
            变量解值或 None / Variable value or None.
        """
        return self.solution.get(name)
