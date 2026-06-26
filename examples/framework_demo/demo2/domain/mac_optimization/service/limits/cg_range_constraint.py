"""CG 范围约束 / CG range constraint.

确保重心在允许的 MAC 范围内。
Ensures CG is within the allowable MAC range.
"""

from __future__ import annotations

from dataclasses import dataclass

from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_constraint import (
    OptimizationConstraint,
)


@dataclass(frozen=True)
class CGRangeParams:
    """CG 范围参数 / CG range parameters.

    描述允许的 CG 范围。
    Describes the allowable CG range.

    Attributes:
        min_percent_mac: 最小 %%MAC / Minimum %%MAC.
        max_percent_mac: 最大 %%MAC / Maximum %%MAC.
        cg_var_name: CG 变量名 / CG variable name.
    """

    min_percent_mac: float
    """最小 %%MAC / Minimum %%MAC."""

    max_percent_mac: float
    """最大 %%MAC / Maximum %%MAC."""

    cg_var_name: str
    """CG 变量名 / CG variable name."""


class CGRangeConstraint:
    """CG 范围约束 / CG range constraint.

    构建线性约束以确保 CG 位置在允许的 %%MAC 范围内。
    生成两个约束:
        cg_var >= min_percent_mac
        cg_var <= max_percent_mac

    Builds linear constraints to ensure the CG position
    is within the allowable %%MAC range. Produces two
    constraints:
        cg_var >= min_percent_mac
        cg_var <= max_percent_mac
    """

    def build_constraints(
        self, params: CGRangeParams
    ) -> tuple[OptimizationConstraint, OptimizationConstraint]:
        """构建 CG 范围约束 / Build CG range constraints.

        Args:
            params: CG 范围参数 / CG range parameters.

        Returns:
            (下界约束, 上界约束) 元组 /
            (lower bound constraint, upper bound constraint) tuple.
        """
        lower = OptimizationConstraint.ge(
            name=f"cg_min_{params.cg_var_name}",
            rhs=params.min_percent_mac,
            coefficients={params.cg_var_name: 1.0},
        )
        upper = OptimizationConstraint.le(
            name=f"cg_max_{params.cg_var_name}",
            rhs=params.max_percent_mac,
            coefficients={params.cg_var_name: 1.0},
        )
        return lower, upper

    def check_solution(
        self,
        *,
        params: CGRangeParams,
        solution: dict[str, float],
    ) -> float:
        """检查解的 CG 范围余量。

        Check CG range margin of a solution.

        Args:
            params: CG 范围参数 / CG range parameters.
            solution: 变量解字典 / Variable solution dict.

        Returns:
            最小余量值（正表示满足，负表示违反）。
            Minimum margin (positive = satisfied,
            negative = violated).
        """
        cg_val = solution.get(params.cg_var_name, 0.0)
        margin_low = cg_val - params.min_percent_mac
        margin_high = params.max_percent_mac - cg_val
        return min(margin_low, margin_high)
