"""优化目标 / Optimization objective.

定义优化问题中的目标函数数据结构。
Defines the data structure for objective functions
in optimization problems.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ObjectiveSense(Enum):
    """优化方向 / Optimization sense.

    描述目标函数的优化方向。
    Describes the optimization direction of
    the objective function.
    """

    MINIMIZE = "min"
    """最小化 / Minimize."""

    MAXIMIZE = "max"
    """最大化 / Maximize."""


@dataclass(frozen=True)
class OptimizationObjective:
    """优化目标 / Optimization objective.

    描述线性目标函数:
        sense * sum(coeff_i * x_i)

    Describes a linear objective function:
        sense * sum(coeff_i * x_i)

    Attributes:
        sense: 优化方向 / Optimization sense.
        coefficients: 系数字典(变量名->系数) /
            Coefficient dict (variable name -> coefficient).
    """

    sense: ObjectiveSense
    """优化方向 / Optimization sense."""

    coefficients: dict[str, float]
    """系数字典 (变量名->系数) /
    Coefficient dict (variable name -> coefficient)."""

    @staticmethod
    def minimize(
        coefficients: dict[str, float],
    ) -> OptimizationObjective:
        """创建最小化目标 / Create minimize objective.

        Args:
            coefficients: 系数 / Coefficients.

        Returns:
            最小化目标实例 / Minimize objective instance.
        """
        return OptimizationObjective(
            sense=ObjectiveSense.MINIMIZE,
            coefficients=coefficients,
        )

    @staticmethod
    def maximize(
        coefficients: dict[str, float],
    ) -> OptimizationObjective:
        """创建最大化目标 / Create maximize objective.

        Args:
            coefficients: 系数 / Coefficients.

        Returns:
            最大化目标实例 / Maximize objective instance.
        """
        return OptimizationObjective(
            sense=ObjectiveSense.MAXIMIZE,
            coefficients=coefficients,
        )

    def evaluate(self, solution: dict[str, float]) -> float:
        """计算目标函数值 / Evaluate objective function.

        Args:
            solution: 变量解字典 / Variable solution dict.

        Returns:
            目标函数值 / Objective function value.
        """
        value = 0.0
        for var_name, coeff in self.coefficients.items():
            val = solution.get(var_name, 0.0)
            value += coeff * val
        return value

    def with_coefficient(
        self,
        *,
        var_name: str,
        coefficient: float,
    ) -> OptimizationObjective:
        """更新单个系数（返回新实例）。

        Update a single coefficient (returns new instance).

        Args:
            var_name: 变量名 / Variable name.
            coefficient: 新系数 / New coefficient.

        Returns:
            更新后的新实例 / New updated instance.
        """
        new_coeffs = {**self.coefficients, var_name: coefficient}
        return OptimizationObjective(
            sense=self.sense,
            coefficients=new_coeffs,
        )

    @property
    def variable_names(self) -> tuple[str, ...]:
        """获取所有变量名 / Get all variable names.

        Returns:
            目标函数涉及的变量名元组。
            Tuple of variable names in the objective.
        """
        return tuple(self.coefficients.keys())
