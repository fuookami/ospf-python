"""载荷最大化管道 / Payload maximization pipeline.

在重量和包线约束下最大化有效载荷。
Maximizes payload within weight and envelope constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...model.payload_result import PayloadResult

if TYPE_CHECKING:
    from ...model.payload_aggregation import PayloadAggregation
    from ...model.payload_context import PayloadContext


@dataclass(frozen=True)
class WeightLimit:
    """重量限制 / Weight limit.

    描述一个重量约束条件。
    Describes a weight constraint condition.

    Attributes:
        limit_id: 限制标识 / Limit identifier.
        max_weight: 最大重量(kg) / Maximum weight (kg).
        current_weight: 当前重量(kg) / Current weight (kg).
    """

    limit_id: str = ""
    max_weight: float = 0.0
    current_weight: float = 0.0

    @property
    def remaining(self) -> float:
        """剩余容量(kg) / Remaining capacity (kg)."""
        return max(0.0, self.max_weight - self.current_weight)

    @property
    def utilization(self) -> float:
        """利用率 / Utilization ratio."""
        if self.max_weight <= 0.0:
            return 1.0
        return self.current_weight / self.max_weight


@dataclass(frozen=True)
class EnvelopeLimit:
    """包线限制 / Envelope limit.

    描述一个飞行包线约束条件。
    Describes a flight envelope constraint condition.

    Attributes:
        envelope_id: 包线标识 / Envelope identifier.
        max_weight: 包线最大重量(kg) /
            Envelope maximum weight (kg).
        min_cg: 最小重心(%MAC) / Min CG (%MAC).
        max_cg: 最大重心(%MAC) / Max CG (%MAC).
        current_cg: 当前重心(%MAC) / Current CG (%MAC).
    """

    envelope_id: str = ""
    max_weight: float = 0.0
    min_cg: float = 0.0
    max_cg: float = 0.0
    current_cg: float = 0.0

    @property
    def cg_feasible(self) -> bool:
        """重心是否可行 / Whether CG is feasible."""
        return self.min_cg <= self.current_cg <= self.max_cg

    @property
    def cg_margin(self) -> float:
        """重心余量(%MAC) / CG margin (%MAC)."""
        to_min = self.current_cg - self.min_cg
        to_max = self.max_cg - self.current_cg
        return min(to_min, to_max)


@dataclass
class PayloadMaximizationPipeline:
    """载荷最大化管道 / Payload maximization pipeline.

    在给定重量限制和包线限制下，计算最大可用载荷。
    综合结构重量限制、包线重量限制和重心包线约束，
    找出最优载荷方案。
    Computes the maximum usable payload under given weight
    and envelope limits. Synthesizes structural weight limits,
    envelope weight limits, and CG envelope constraints to
    find the optimal payload solution.

    Attributes:
        context: 载荷上下文 / Payload context.
        _results: 内部结果收集 / Internal result collection.
    """

    context: PayloadContext
    _results: list[PayloadResult] = field(
        default_factory=list,
        init=False,
    )

    def run(
        self,
        *,
        weight_limits: tuple[WeightLimit, ...],
        envelope_limits: tuple[EnvelopeLimit, ...],
        fuel_weight: float = 0.0,
        crew_weight: float = 0.0,
    ) -> PayloadResult:
        """运行载荷最大化管道。

        Run the payload maximization pipeline.

        Args:
            weight_limits: 重量限制集合 /
                Weight limit collection.
            envelope_limits: 包线限制集合 /
                Envelope limit collection.
            fuel_weight: 燃油重量(kg) / Fuel weight (kg).
            crew_weight: 机组重量(kg) / Crew weight (kg).

        Returns:
            载荷最大化结果 / Payload maximization result.
        """
        self._results.clear()

        oew = self.context.operating_empty_weight
        fixed_weight = oew + fuel_weight + crew_weight

        weight_result = self._check_weight_limits(
            weight_limits=weight_limits,
            fixed_weight=fixed_weight,
        )
        if weight_result is not None:
            self._results.append(weight_result)

        envelope_result = self._check_envelope_limits(
            envelope_limits=envelope_limits,
            fixed_weight=fixed_weight,
        )
        if envelope_result is not None:
            self._results.append(envelope_result)

        return self._select_best()

    def _check_weight_limits(
        self,
        *,
        weight_limits: tuple[WeightLimit, ...],
        fixed_weight: float,
    ) -> PayloadResult | None:
        """校验重量限制 / Check weight limits.

        Args:
            weight_limits: 重量限制集合 / Weight limits.
            fixed_weight: 固定重量(kg) / Fixed weight (kg).

        Returns:
            载荷结果或 None / Payload result or None.
        """
        if not weight_limits:
            return None

        min_remaining = min(lim.remaining for lim in weight_limits)
        max_payload = max(0.0, min_remaining)

        if max_payload <= 0.0:
            tightest = min(
                weight_limits,
                key=lambda l: l.remaining,
            )
            return PayloadResult.create_infeasible(
                limiting_factor=(
                    f"weight:{tightest.limit_id}:remaining={tightest.remaining:.1f}kg"
                ),
            )

        structural = self.context.max_structural_weight
        envelope = self.context.max_envelope_weight
        weight_margin = max(
            0.0,
            structural - fixed_weight - max_payload,
        )
        env_margin = max(
            0.0,
            envelope - fixed_weight - max_payload,
        )

        return PayloadResult.create_feasible(
            max_payload=max_payload,
            weight_margin=weight_margin,
            envelope_margin=env_margin,
        )

    def _check_envelope_limits(
        self,
        *,
        envelope_limits: tuple[EnvelopeLimit, ...],
        fixed_weight: float,
    ) -> PayloadResult | None:
        """校验包线限制 / Check envelope limits.

        Args:
            envelope_limits: 包线限制集合 / Envelope limits.
            fixed_weight: 固定重量(kg) / Fixed weight (kg).

        Returns:
            载荷结果或 None / Payload result or None.
        """
        if not envelope_limits:
            return None

        feasible_limits = tuple(lim for lim in envelope_limits if lim.cg_feasible)
        if not feasible_limits:
            return PayloadResult.create_infeasible(
                limiting_factor="envelope:cg_out_of_range",
            )

        min_env_weight = min(lim.max_weight for lim in feasible_limits)
        max_payload = max(0.0, min_env_weight - fixed_weight)

        if max_payload <= 0.0:
            return PayloadResult.create_infeasible(
                limiting_factor=(f"envelope:max_weight={min_env_weight:.1f}kg"),
            )

        best_cg_margin = max(lim.cg_margin for lim in feasible_limits)

        return PayloadResult.create_feasible(
            max_payload=max_payload,
            weight_margin=max_payload,
            envelope_margin=best_cg_margin,
        )

    def _select_best(self) -> PayloadResult:
        """选择最优结果 / Select best result.

        Returns:
            最大载荷的可行结果，若无可行结果则返回
            第一个不可行结果。
            Feasible result with largest payload; first
            infeasible result if none feasible.
        """
        if not self._results:
            return PayloadResult.create_infeasible(
                limiting_factor="no_limits_configured",
            )

        feasible = tuple(r for r in self._results if r.feasible)
        if feasible:
            return max(
                feasible,
                key=lambda r: r.max_payload,
            )
        return self._results[0]

    def compute_all_scenarios(
        self,
        *,
        weight_limits: tuple[WeightLimit, ...],
        envelope_limits: tuple[EnvelopeLimit, ...],
        fuel_weights: tuple[float, ...],
        crew_weight: float = 0.0,
    ) -> PayloadAggregation:
        """计算多个燃油场景 / Compute multiple fuel scenarios.

        Args:
            weight_limits: 重量限制集合 / Weight limits.
            envelope_limits: 包线限制集合 / Envelope limits.
            fuel_weights: 燃油重量列表 / Fuel weight list.
            crew_weight: 机组重量(kg) / Crew weight (kg).

        Returns:
            所有场景的聚合结果 / Aggregation of all scenarios.
        """
        from ...model.payload_aggregation import (
            PayloadAggregation,
        )

        results: list[PayloadResult] = []
        for fw in fuel_weights:
            result = self.run(
                weight_limits=weight_limits,
                envelope_limits=envelope_limits,
                fuel_weight=fw,
                crew_weight=crew_weight,
            )
            results.append(result)
        return PayloadAggregation(results=tuple(results))
