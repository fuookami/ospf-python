"""MAC 优化管道 / MAC optimization pipeline.

组合所有 MAC 优化约束为统一管道。
Composes all MAC optimization constraints into
a unified pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.mac_optimization.service.limits.cg_range_constraint import (
    CGRangeConstraint,
    CGRangeParams,
)
from examples.framework_demo.demo2.domain.mac_optimization.service.limits.stability_margin_constraint import (
    StabilityMarginConstraint,
    StabilityMarginParams,
)
from examples.framework_demo.demo2.domain.mac_optimization.service.limits.trim_constraint import (
    TrimConstraint,
    TrimParams,
)
from examples.framework_demo.demo2.domain.mac_optimization.service.limits.weight_limit_constraint import (
    WeightLimitConstraint,
    WeightLimitParams,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.mac_optimization.model.mac_optimization_context import (
        MACOptimizationContext,
    )
    from examples.framework_demo.demo2.domain.mac_optimization.model.optimization_constraint import (
        OptimizationConstraint,
    )


@dataclass
class MACOptimizationPipeline:
    """MAC 优化管道 / MAC optimization pipeline.

    按顺序执行 CG 范围、重量限制、配平力、稳定性裕度
    等约束构建，将所有约束合并到优化上下文中。
    Executes CG range, weight limit, trim force, and
    stability margin constraint building in sequence,
    merging all constraints into the optimization context.

    Attributes:
        context: MAC 优化上下文 / MAC optimization context.
        _constraints: 内部约束收集 / Internal constraint collection.
    """

    context: MACOptimizationContext
    """MAC 优化上下文 / MAC optimization context."""

    _constraints: list[OptimizationConstraint] = field(default_factory=list, init=False)

    def run(
        self,
        *,
        cg_params: CGRangeParams,
        weight_params: tuple[WeightLimitParams, ...] = (),
        trim_params: tuple[tuple[TrimParams, float], ...] = (),
        stability_params: tuple[StabilityMarginParams, ...] = (),
    ) -> MACOptimizationContext:
        """运行 MAC 优化管道 / Run MAC optimization pipeline.

        Args:
            cg_params: CG 范围参数 / CG range params.
            weight_params: 重量限制参数元组 /
                Tuple of weight limit params.
            trim_params: (配平力参数, 重量值) 元组 /
                Tuple of (trim params, weight value).
            stability_params: 稳定性裕度参数元组 /
                Tuple of stability margin params.

        Returns:
            包含所有约束的新上下文 /
            New context with all constraints.
        """
        self._constraints.clear()

        self._build_cg_constraints(cg_params)
        self._build_weight_constraints(weight_params)
        self._build_trim_constraints(trim_params)
        self._build_stability_constraints(stability_params)

        return self._apply_constraints()

    def _build_cg_constraints(self, params: CGRangeParams) -> None:
        """构建 CG 范围约束 / Build CG range constraints.

        Args:
            params: CG 范围参数 / CG range params.
        """
        builder = CGRangeConstraint()
        lower, upper = builder.build_constraints(params)
        self._constraints.append(lower)
        self._constraints.append(upper)

    def _build_weight_constraints(
        self,
        params_list: tuple[WeightLimitParams, ...],
    ) -> None:
        """构建重量限制约束 / Build weight limit constraints.

        Args:
            params_list: 重量限制参数元组 /
                Tuple of weight limit params.
        """
        builder = WeightLimitConstraint()
        constraints = builder.build_batch_constraints(params_list)
        self._constraints.extend(constraints)

    def _build_trim_constraints(
        self,
        params_list: tuple[tuple[TrimParams, float], ...],
    ) -> None:
        """构建配平力约束 / Build trim force constraints.

        Args:
            params_list: (配平力参数, 重量值) 元组 /
                Tuple of (trim params, weight value).
        """
        builder = TrimConstraint()
        for params, weight_value in params_list:
            lower, upper = builder.build_constraints(
                params=params,
                weight_value=weight_value,
            )
            self._constraints.append(lower)
            self._constraints.append(upper)

    def _build_stability_constraints(
        self,
        params_list: tuple[StabilityMarginParams, ...],
    ) -> None:
        """构建稳定性裕度约束。

        Build stability margin constraints.

        Args:
            params_list: 稳定性裕度参数元组 /
                Tuple of stability margin params.
        """
        builder = StabilityMarginConstraint()
        for params in params_list:
            lower, upper = builder.build_constraints(params)
            self._constraints.append(lower)
            self._constraints.append(upper)

    def _apply_constraints(
        self,
    ) -> MACOptimizationContext:
        """将约束应用到上下文 / Apply constraints to context.

        Returns:
            包含所有约束的新上下文 /
            New context with all constraints.
        """
        ctx = self.context
        for constraint in self._constraints:
            ctx = ctx.register_constraint(constraint)
        return ctx

    def validate_all(
        self,
        *,
        cg_params: CGRangeParams,
        weight_params: tuple[WeightLimitParams, ...] = (),
        trim_params: tuple[tuple[TrimParams, float], ...] = (),
        stability_params: tuple[StabilityMarginParams, ...] = (),
        solution: dict[str, float],
    ) -> dict[str, float]:
        """校验所有约束余量 / Validate all constraint margins.

        Args:
            cg_params: CG 范围参数 / CG range params.
            weight_params: 重量限制参数 / Weight limit params.
            trim_params: 配平力参数元组 / Trim params tuples.
            stability_params: 稳定性裕度参数 / Stability params.
            solution: 变量解字典 / Variable solution dict.

        Returns:
            约束名->余量 字典 / Constraint name -> margin dict.
        """
        margins: dict[str, float] = {}

        # CG 范围 / CG range
        cg_builder = CGRangeConstraint()
        cg_margin = cg_builder.check_solution(params=cg_params, solution=solution)
        margins["cg_range"] = cg_margin

        # 重量限制 / Weight limits
        w_builder = WeightLimitConstraint()
        w_margins = w_builder.check_all(params_list=weight_params, solution=solution)
        margins.update(w_margins)

        # 配平力 / Trim force
        t_builder = TrimConstraint()
        for t_params, weight_val in trim_params:
            t_margin = t_builder.check_solution(
                params=t_params,
                weight_value=weight_val,
                solution=solution,
            )
            margins[f"trim_{t_params.cg_var_name}"] = t_margin

        # 稳定性裕度 / Stability margin
        s_builder = StabilityMarginConstraint()
        for s_params in stability_params:
            s_margin = s_builder.check_solution(params=s_params, solution=solution)
            margins[f"stability_{s_params.cg_var_name}"] = s_margin

        return margins
