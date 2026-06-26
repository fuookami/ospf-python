"""优化约束 / Optimization constraint.

定义优化问题中的约束数据结构。
Defines the data structure for constraints
in optimization problems.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ConstraintSense(Enum):
    """约束方向 / Constraint sense.

    描述约束的不等式方向。
    Describes the inequality direction of a constraint.
    """

    LESS_EQUAL = "<="
    """小于等于 / Less than or equal."""

    EQUAL = "=="
    """等于 / Equal."""

    GREATER_EQUAL = ">="
    """大于等于 / Greater than or equal."""


@dataclass(frozen=True)
class OptimizationConstraint:
    """优化约束 / Optimization constraint.

    描述一个线性约束，形式为:
        sense(coeffs * variables, rhs)
    例如: sum(c_i * x_i) <= rhs

    Describes a linear constraint of the form:
        sense(coeffs * variables, rhs)
    E.g.: sum(c_i * x_i) <= rhs

    Attributes:
        name: 约束名 / Constraint name.
        sense: 约束方向 / Constraint sense.
        rhs: 右端值 / Right-hand side value.
        coefficients: 系数字典(变量名->系数) /
            Coefficient dict (variable name -> coefficient).
    """

    name: str
    """约束名 / Constraint name."""

    sense: ConstraintSense
    """约束方向 / Constraint sense."""

    rhs: float
    """右端值 / Right-hand side value."""

    coefficients: dict[str, float]
    """系数字典 (变量名->系数) /
    Coefficient dict (variable name -> coefficient)."""

    @staticmethod
    def le(
        *,
        name: str,
        rhs: float,
        coefficients: dict[str, float],
    ) -> OptimizationConstraint:
        """创建 <= 约束 / Create <= constraint.

        Args:
            name: 约束名 / Constraint name.
            rhs: 右端值 / Right-hand side.
            coefficients: 系数 / Coefficients.

        Returns:
            <= 约束实例 / <= constraint instance.
        """
        return OptimizationConstraint(
            name=name,
            sense=ConstraintSense.LESS_EQUAL,
            rhs=rhs,
            coefficients=coefficients,
        )

    @staticmethod
    def eq(
        *,
        name: str,
        rhs: float,
        coefficients: dict[str, float],
    ) -> OptimizationConstraint:
        """创建 == 约束 / Create == constraint.

        Args:
            name: 约束名 / Constraint name.
            rhs: 右端值 / Right-hand side.
            coefficients: 系数 / Coefficients.

        Returns:
            == 约束实例 / == constraint instance.
        """
        return OptimizationConstraint(
            name=name,
            sense=ConstraintSense.EQUAL,
            rhs=rhs,
            coefficients=coefficients,
        )

    @staticmethod
    def ge(
        *,
        name: str,
        rhs: float,
        coefficients: dict[str, float],
    ) -> OptimizationConstraint:
        """创建 >= 约束 / Create >= constraint.

        Args:
            name: 约束名 / Constraint name.
            rhs: 右端值 / Right-hand side.
            coefficients: 系数 / Coefficients.

        Returns:
            >= 约束实例 / >= constraint instance.
        """
        return OptimizationConstraint(
            name=name,
            sense=ConstraintSense.GREATER_EQUAL,
            rhs=rhs,
            coefficients=coefficients,
        )

    def evaluate(self, solution: dict[str, float]) -> float:
        """计算约束左端值 / Evaluate constraint LHS.

        Args:
            solution: 变量解字典 / Variable solution dict.

        Returns:
            左端值与右端值之差。正值表示满足约束。
            Difference of LHS and RHS. Positive means
            the constraint is satisfied.
        """
        lhs = 0.0
        for var_name, coeff in self.coefficients.items():
            val = solution.get(var_name, 0.0)
            lhs += coeff * val

        if self.sense == ConstraintSense.LESS_EQUAL:
            return self.rhs - lhs
        if self.sense == ConstraintSense.GREATER_EQUAL:
            return lhs - self.rhs
        # EQUAL: 返回绝对值的负数，表示违反量
        return -abs(lhs - self.rhs)

    def is_satisfied(
        self,
        solution: dict[str, float],
        tolerance: float = 1e-6,
    ) -> bool:
        """检查约束是否满足 / Check if constraint is satisfied.

        Args:
            solution: 变量解字典 / Variable solution dict.
            tolerance: 容差 / Tolerance.

        Returns:
            满足约束返回 True / True if constraint satisfied.
        """
        return self.evaluate(solution) >= -tolerance
