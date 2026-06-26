"""稳定性裕度约束 / Stability margin constraint.

确保静稳定性裕度满足要求。
Ensures the static stability margin meets requirements.
"""

from __future__ import annotations

from dataclasses import dataclass

from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_constraint import (
    OptimizationConstraint,
)


@dataclass(frozen=True)
class StabilityMarginParams:
    """稳定性裕度参数 / Stability margin parameters.

    描述静稳定性裕度约束参数。
    Describes the static stability margin parameters.

    Attributes:
        min_margin: 最小裕度 (%%MAC) / Min margin (%%MAC).
        max_margin: 最大裕度 (%%MAC) / Max margin (%%MAC).
        neutral_point: 中性点 (%%MAC) / Neutral point (%%MAC).
        cg_var_name: CG 变量名 / CG variable name.
    """

    min_margin: float
    """最小裕度 (%%MAC) / Min margin (%%MAC)."""

    max_margin: float
    """最大裕度 (%%MAC) / Max margin (%%MAC)."""

    neutral_point: float
    """中性点 (%%MAC) / Neutral point (%%MAC)."""

    cg_var_name: str
    """CG 变量名 / CG variable name."""


class StabilityMarginConstraint:
    """稳定性裕度约束 / Stability margin constraint.

    静稳定性裕度定义:
        margin = neutral_point - cg_position

    构建约束:
        neutral_point - cg_var >= min_margin  (cg_var <= NP - min)
        neutral_point - cg_var <= max_margin  (cg_var >= NP - max)

    Static stability margin definition:
        margin = neutral_point - cg_position

    Builds constraints:
        neutral_point - cg_var >= min_margin (cg_var <= NP - min)
        neutral_point - cg_var <= max_margin (cg_var >= NP - max)
    """

    def build_constraints(
        self, params: StabilityMarginParams
    ) -> tuple[OptimizationConstraint, OptimizationConstraint]:
        """构建稳定性裕度约束。

        Build stability margin constraints.

        Args:
            params: 稳定性裕度参数 / Stability margin params.

        Returns:
            (最小裕度约束, 最大裕度约束) 元组 /
            (min margin constraint, max margin constraint) tuple.
        """
        # margin = NP - cg_var >= min_margin
        # => -cg_var >= min_margin - NP
        # => cg_var <= NP - min_margin
        min_margin_constraint = OptimizationConstraint.le(
            name=f"stab_margin_min_{params.cg_var_name}",
            rhs=params.neutral_point - params.min_margin,
            coefficients={params.cg_var_name: 1.0},
        )

        # margin = NP - cg_var <= max_margin
        # => -cg_var <= max_margin - NP
        # => cg_var >= NP - max_margin
        max_margin_constraint = OptimizationConstraint.ge(
            name=f"stab_margin_max_{params.cg_var_name}",
            rhs=params.neutral_point - params.max_margin,
            coefficients={params.cg_var_name: 1.0},
        )

        return min_margin_constraint, max_margin_constraint

    def evaluate_margin(
        self,
        *,
        params: StabilityMarginParams,
        cg_value: float,
    ) -> float:
        """计算稳定性裕度 / Calculate stability margin.

        Args:
            params: 稳定性裕度参数 / Stability margin params.
            cg_value: CG 值 (%%MAC) / CG value (%%MAC).

        Returns:
            稳定性裕度 (%%MAC) / Stability margin (%%MAC).
        """
        return params.neutral_point - cg_value

    def check_solution(
        self,
        *,
        params: StabilityMarginParams,
        solution: dict[str, float],
    ) -> float:
        """检查解的稳定性裕度余量。

        Check stability margin of a solution.

        Args:
            params: 稳定性裕度参数 / Stability margin params.
            solution: 变量解字典 / Variable solution dict.

        Returns:
            最小余量（正表示满足，负表示违反）。
            Minimum margin (positive = satisfied,
            negative = violated).
        """
        cg_val = solution.get(params.cg_var_name, 0.0)
        margin = self.evaluate_margin(params=params, cg_value=cg_val)
        margin_low = margin - params.min_margin
        margin_high = params.max_margin - margin
        return min(margin_low, margin_high)
