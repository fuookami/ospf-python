"""配平力约束 / Trim force constraint.

确保配平力满足飞行控制要求。
Ensures trim forces meet flight control requirements.
"""

from __future__ import annotations

from dataclasses import dataclass

from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_constraint import (
    OptimizationConstraint,
)


@dataclass(frozen=True)
class TrimParams:
    """配平力参数 / Trim force parameters.

    描述配平力约束所需的参数。
    Describes the parameters for trim force constraints.

    Attributes:
        min_trim_force: 最小配平力 (N) / Min trim force (N).
        max_trim_force: 最大配平力 (N) / Max trim force (N).
        cg_var_name: CG 变量名 / CG variable name.
        weight_var_name: 重量变量名 / Weight variable name.
        moment_arm: 力臂系数 / Moment arm coefficient.
    """

    min_trim_force: float
    """最小配平力 (N) / Min trim force (N)."""

    max_trim_force: float
    """最大配平力 (N) / Max trim force (N)."""

    cg_var_name: str
    """CG 变量名 / CG variable name."""

    weight_var_name: str
    """重量变量名 / Weight variable name."""

    moment_arm: float
    """力臂系数 (N*m/kg/%MAC) /
    Moment arm coefficient (N*m/kg/%%MAC)."""


class TrimConstraint:
    """配平力约束 / Trim force constraint.

    配平力公式:
        trim_force = moment_arm * weight * cg_offset

    其中 cg_offset 为 CG 相对铰链点的偏移量。
    构建约束:
        moment_arm * weight * cg_var >= min_trim_force
        moment_arm * weight * cg_var <= max_trim_force

    Trim force formula:
        trim_force = moment_arm * weight * cg_offset

    Where cg_offset is the CG offset from the hinge point.
    Builds constraints:
        moment_arm * weight * cg_var >= min_trim_force
        moment_arm * weight * cg_var <= max_trim_force

    注意：由于 weight * cg_var 为非线性项，这里
    将 weight 固定为参数值，仅对 cg_var 建立线性约束。
    Note: Since weight * cg_var is nonlinear, we treat
    weight as a parameter and build linear constraints
    on cg_var only.
    """

    def build_constraints(
        self,
        *,
        params: TrimParams,
        weight_value: float,
    ) -> tuple[OptimizationConstraint, OptimizationConstraint]:
        """构建配平力约束 / Build trim force constraints.

        Args:
            params: 配平力参数 / Trim force parameters.
            weight_value: 当前重量值 (kg) / Current weight (kg).

        Returns:
            (下界约束, 上界约束) 元组 /
            (lower bound, upper bound) constraint tuple.
        """
        # 线性化: trim = arm * weight_val * cg_var
        coeff = params.moment_arm * weight_value

        lower = OptimizationConstraint.ge(
            name=f"trim_min_{params.cg_var_name}",
            rhs=params.min_trim_force,
            coefficients={params.cg_var_name: coeff},
        )
        upper = OptimizationConstraint.le(
            name=f"trim_max_{params.cg_var_name}",
            rhs=params.max_trim_force,
            coefficients={params.cg_var_name: coeff},
        )
        return lower, upper

    def evaluate_trim_force(
        self,
        *,
        params: TrimParams,
        weight_value: float,
        cg_value: float,
    ) -> float:
        """计算配平力 / Calculate trim force.

        Args:
            params: 配平力参数 / Trim force parameters.
            weight_value: 重量 (kg) / Weight (kg).
            cg_value: CG 值 (%%MAC) / CG value (%%MAC).

        Returns:
            配平力 (N) / Trim force (N).
        """
        return params.moment_arm * weight_value * cg_value

    def check_solution(
        self,
        *,
        params: TrimParams,
        weight_value: float,
        solution: dict[str, float],
    ) -> float:
        """检查解的配平力余量。

        Check trim force margin of a solution.

        Args:
            params: 配平力参数 / Trim force parameters.
            weight_value: 重量 (kg) / Weight (kg).
            solution: 变量解字典 / Variable solution dict.

        Returns:
            最小余量（正表示满足，负表示违反）。
            Minimum margin (positive = satisfied,
            negative = violated).
        """
        cg_val = solution.get(params.cg_var_name, 0.0)
        trim = self.evaluate_trim_force(
            params=params,
            weight_value=weight_value,
            cg_value=cg_val,
        )
        margin_low = trim - params.min_trim_force
        margin_high = params.max_trim_force - trim
        return min(margin_low, margin_high)
