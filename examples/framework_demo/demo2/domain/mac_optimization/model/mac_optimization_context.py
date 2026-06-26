"""MAC 优化上下文 / MAC optimization context.

封装 MAC/CG 优化问题的运行时状态。
Encapsulates the runtime state of MAC/CG
optimization problems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.mac_optimization.model.mac_optimization_aggregation import (
    MACOptimizationAggregation,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_constraint import (
        OptimizationConstraint,
    )
    from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_objective import (
        OptimizationObjective,
    )
    from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_variable import (
        OptimizationVariable,
    )


@dataclass(frozen=True)
class MACOptimizationContext:
    """MAC 优化上下文 / MAC optimization context.

    持有优化问题的聚合数据和目标函数，
    提供注册变量、约束和查找功能。
    Holds the optimization problem's aggregated data and
    objective function, with methods to register variables,
    constraints, and perform lookups.

    Attributes:
        aggregation: MAC 优化聚合 / MAC optimization aggregation.
        objective: 优化目标 / Optimization objective.
        aircraft_type: 机型代码 / Aircraft type code.
    """

    aggregation: MACOptimizationAggregation
    """MAC 优化聚合 / MAC optimization aggregation."""

    objective: OptimizationObjective
    """优化目标 / Optimization objective."""

    aircraft_type: str
    """机型代码 / Aircraft type code."""

    @staticmethod
    def create(
        *,
        aggregation: MACOptimizationAggregation,
        objective: OptimizationObjective,
        aircraft_type: str,
    ) -> MACOptimizationContext:
        """创建 MAC 优化上下文 / Create context.

        Args:
            aggregation: MAC 优化聚合 / Aggregation.
            objective: 优化目标 / Objective.
            aircraft_type: 机型代码 / Aircraft type code.

        Returns:
            MAC 优化上下文实例 / Context instance.
        """
        return MACOptimizationContext(
            aggregation=aggregation,
            objective=objective,
            aircraft_type=aircraft_type,
        )

    @staticmethod
    def empty(
        *,
        aircraft_type: str,
        objective: OptimizationObjective,
    ) -> MACOptimizationContext:
        """创建空上下文 / Create empty context.

        Args:
            aircraft_type: 机型代码 / Aircraft type code.
            objective: 优化目标 / Objective.

        Returns:
            空的 MAC 优化上下文 / Empty context.
        """
        return MACOptimizationContext(
            aggregation=MACOptimizationAggregation.empty(),
            objective=objective,
            aircraft_type=aircraft_type,
        )

    def register_variable(
        self, variable: OptimizationVariable
    ) -> MACOptimizationContext:
        """注册变量（返回新上下文）。

        Register variable (returns new context).

        Args:
            variable: 待注册的变量 / Variable to register.

        Returns:
            包含新变量的新上下文 /
            New context with registered variable.
        """
        return MACOptimizationContext(
            aggregation=self.aggregation.add_variable(variable),
            objective=self.objective,
            aircraft_type=self.aircraft_type,
        )

    def register_constraint(
        self, constraint: OptimizationConstraint
    ) -> MACOptimizationContext:
        """注册约束（返回新上下文）。

        Register constraint (returns new context).

        Args:
            constraint: 待注册的约束 / Constraint to register.

        Returns:
            包含新约束的新上下文 /
            New context with registered constraint.
        """
        return MACOptimizationContext(
            aggregation=self.aggregation.add_constraint(constraint),
            objective=self.objective,
            aircraft_type=self.aircraft_type,
        )

    def lookup_variable(self, name: str) -> OptimizationVariable | None:
        """查找变量 / Lookup variable.

        Args:
            name: 变量名 / Variable name.

        Returns:
            匹配的变量或 None / Matching variable or None.
        """
        return self.aggregation.find_variable(name)

    def lookup_constraint(self, name: str) -> OptimizationConstraint | None:
        """查找约束 / Lookup constraint.

        Args:
            name: 约束名 / Constraint name.

        Returns:
            匹配的约束或 None / Matching constraint or None.
        """
        return self.aggregation.find_constraint(name)

    @property
    def has_variables(self) -> bool:
        """是否有注册的变量 / Whether variables registered.

        Returns:
            有变量时返回 True / True if variables exist.
        """
        return self.aggregation.variable_count > 0

    @property
    def has_constraints(self) -> bool:
        """是否有注册的约束 / Whether constraints registered.

        Returns:
            有约束时返回 True / True if constraints exist.
        """
        return self.aggregation.constraint_count > 0

    @property
    def total_coefficients(self) -> int:
        """所有约束和目标中的系数总数。

        Total number of coefficients across all
        constraints and objective.

        Returns:
            系数总数 / Total coefficient count.
        """
        count = len(self.objective.coefficients)
        for c in self.aggregation.constraints:
            count += len(c.coefficients)
        return count
