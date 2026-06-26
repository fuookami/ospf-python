"""重量限制约束 / Weight limit constraint.

确保各站位重量在允许范围内。
Ensures weight at each station is within allowable limits.
"""

from __future__ import annotations

from dataclasses import dataclass

from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_constraint import (
    OptimizationConstraint,
)


@dataclass(frozen=True)
class WeightLimitParams:
    """重量限制参数 / Weight limit parameters.

    描述单个站位的重量限制。
    Describes the weight limit for a single station.

    Attributes:
        station_name: 站位名称 / Station name.
        max_weight: 最大允许重量 (kg) / Max allowable weight (kg).
        weight_var_name: 重量变量名 / Weight variable name.
    """

    station_name: str
    """站位名称 / Station name."""

    max_weight: float
    """最大允许重量 (kg) / Max allowable weight (kg)."""

    weight_var_name: str
    """重量变量名 / Weight variable name."""


class WeightLimitConstraint:
    """重量限制约束 / Weight limit constraint.

    构建线性约束以确保各站位载荷不超过最大允许重量。
    形式: weight_var <= max_weight

    Builds linear constraints to ensure station loads
    do not exceed the maximum allowable weight.
    Form: weight_var <= max_weight
    """

    def build_constraint(self, params: WeightLimitParams) -> OptimizationConstraint:
        """构建重量限制约束 / Build weight limit constraint.

        Args:
            params: 重量限制参数 / Weight limit parameters.

        Returns:
            重量限制约束 / Weight limit constraint.
        """
        return OptimizationConstraint.le(
            name=f"weight_max_{params.station_name}",
            rhs=params.max_weight,
            coefficients={params.weight_var_name: 1.0},
        )

    def build_batch_constraints(
        self,
        params_list: tuple[WeightLimitParams, ...],
    ) -> tuple[OptimizationConstraint, ...]:
        """批量构建重量限制约束。

        Build weight limit constraints in batch.

        Args:
            params_list: 重量限制参数元组 /
                Tuple of weight limit parameters.

        Returns:
            重量限制约束元组 / Tuple of weight constraints.
        """
        return tuple(self.build_constraint(p) for p in params_list)

    def check_solution(
        self,
        *,
        params: WeightLimitParams,
        solution: dict[str, float],
    ) -> float:
        """检查解的重量余量。

        Check weight margin of a solution.

        Args:
            params: 重量限制参数 / Weight limit parameters.
            solution: 变量解字典 / Variable solution dict.

        Returns:
            重量余量（正表示满足，负表示违反）。
            Weight margin (positive = satisfied,
            negative = violated).
        """
        weight_val = solution.get(params.weight_var_name, 0.0)
        return params.max_weight - weight_val

    def check_all(
        self,
        *,
        params_list: tuple[WeightLimitParams, ...],
        solution: dict[str, float],
    ) -> dict[str, float]:
        """检查所有站位的重量余量。

        Check weight margins for all stations.

        Args:
            params_list: 重量限制参数元组 /
                Tuple of weight limit parameters.
            solution: 变量解字典 / Variable solution dict.

        Returns:
            站位名->余量 字典 /
            Station name -> margin dict.
        """
        return {
            p.station_name: self.check_solution(params=p, solution=solution)
            for p in params_list
        }
