"""MAC 优化聚合 / MAC optimization aggregation.

管理优化问题中变量和约束的聚合。
Aggregation of variables and constraints in
optimization problems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_constraint import (
        OptimizationConstraint,
    )
    from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_variable import (
        OptimizationVariable,
    )


@dataclass(frozen=True)
class MACOptimizationAggregation:
    """MAC 优化聚合 / MAC optimization aggregation.

    将优化问题的所有变量和约束聚合为一个集合，
    提供便捷的查询方法。
    Aggregates all variables and constraints of an
    optimization problem into a collection with
    convenient query methods.

    Attributes:
        variables: 优化变量元组 / Tuple of optimization variables.
        constraints: 优化约束元组 / Tuple of optimization constraints.
    """

    variables: tuple[OptimizationVariable, ...]
    """优化变量元组 / Tuple of optimization variables."""

    constraints: tuple[OptimizationConstraint, ...]
    """优化约束元组 / Tuple of optimization constraints."""

    @staticmethod
    def create(
        *,
        variables: tuple[OptimizationVariable, ...],
        constraints: tuple[OptimizationConstraint, ...],
    ) -> MACOptimizationAggregation:
        """创建 MAC 优化聚合 / Create MAC optimization aggregation.

        Args:
            variables: 优化变量元组 / Tuple of variables.
            constraints: 优化约束元组 / Tuple of constraints.

        Returns:
            MAC 优化聚合实例 / Aggregation instance.
        """
        return MACOptimizationAggregation(
            variables=variables,
            constraints=constraints,
        )

    @staticmethod
    def empty() -> MACOptimizationAggregation:
        """创建空聚合 / Create empty aggregation.

        Returns:
            空的 MAC 优化聚合 / Empty aggregation.
        """
        return MACOptimizationAggregation(
            variables=(),
            constraints=(),
        )

    @property
    def variable_count(self) -> int:
        """变量数量 / Variable count.

        Returns:
            变量数量 / Number of variables.
        """
        return len(self.variables)

    @property
    def constraint_count(self) -> int:
        """约束数量 / Constraint count.

        Returns:
            约束数量 / Number of constraints.
        """
        return len(self.constraints)

    def find_variable(self, name: str) -> OptimizationVariable | None:
        """按名称查找变量 / Find variable by name.

        Args:
            name: 变量名 / Variable name.

        Returns:
            匹配的变量或 None / Matching variable or None.
        """
        for v in self.variables:
            if v.name == name:
                return v
        return None

    def find_constraint(self, name: str) -> OptimizationConstraint | None:
        """按名称查找约束 / Find constraint by name.

        Args:
            name: 约束名 / Constraint name.

        Returns:
            匹配的约束或 None / Matching constraint or None.
        """
        for c in self.constraints:
            if c.name == name:
                return c
        return None

    @property
    def variable_names(self) -> tuple[str, ...]:
        """获取所有变量名 / Get all variable names.

        Returns:
            变量名元组 / Tuple of variable names.
        """
        return tuple(v.name for v in self.variables)

    @property
    def constraint_names(self) -> tuple[str, ...]:
        """获取所有约束名 / Get all constraint names.

        Returns:
            约束名元组 / Tuple of constraint names.
        """
        return tuple(c.name for c in self.constraints)

    def add_variable(
        self, variable: OptimizationVariable
    ) -> MACOptimizationAggregation:
        """添加变量（返回新聚合）。

        Add variable (returns new aggregation).

        Args:
            variable: 待添加的变量 / Variable to add.

        Returns:
            包含新变量的新聚合 / New aggregation with added variable.
        """
        return MACOptimizationAggregation(
            variables=self.variables + (variable,),
            constraints=self.constraints,
        )

    def add_constraint(
        self, constraint: OptimizationConstraint
    ) -> MACOptimizationAggregation:
        """添加约束（返回新聚合）。

        Add constraint (returns new aggregation).

        Args:
            constraint: 待添加的约束 / Constraint to add.

        Returns:
            包含新约束的新聚合 /
            New aggregation with added constraint.
        """
        return MACOptimizationAggregation(
            variables=self.variables,
            constraints=self.constraints + (constraint,),
        )
