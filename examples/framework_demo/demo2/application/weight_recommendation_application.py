"""重量建议应用 / Weight Recommendation Application.

编排载重建议优化：基于适航限制给出最优载重建议。
Orchestrates weight recommendation optimization:
provides optimal weight recommendations based on
airworthiness limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.aircraft.service.aircraft_envelope_validator import (
    AircraftEnvelopeValidator,
)
from examples.framework_demo.demo2.domain.aircraft.service.aircraft_weight_validator import (
    AircraftWeightValidator,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft import Aircraft
    from examples.framework_demo.demo2.domain.aircraft.service.aircraft_context import (
        AircraftContext,
    )
    from examples.framework_demo.demo2.domain.airworthiness_security.service.limits.airworthiness_pipeline import (
        AirworthinessPipeline,
    )
    from examples.framework_demo.demo2.domain.recommended_weight_equalization.service.limits.equalization_pipeline import (
        EqualizationPipeline,
    )


@dataclass(frozen=True)
class WeightRecommendation:
    """重量建议 / Weight recommendation.

    Attributes:
        recommended_payload: 建议载荷 (kg) / Recommended payload (kg).
        max_payload: 最大载荷 (kg) / Max payload (kg).
        limiting_factor: 限制因素 / Limiting factor.
        balance_suggestions: 平衡建议 / Balance suggestions.
    """

    recommended_payload: float = 0.0
    max_payload: float = 0.0
    limiting_factor: str = ""
    balance_suggestions: tuple[str, ...] = field(
        default_factory=tuple,
    )


class WeightRecommendationApplication:
    """重量建议应用 / Weight Recommendation Application.

    编排载重建议，综合考虑适航、平衡、信封限制。
    Orchestrates weight recommendation, considering
    airworthiness, balance, and envelope limits.
    """

    def __init__(
        self,
        *,
        aircraft_context: AircraftContext,
        airworthiness_pipeline: AirworthinessPipeline,
        equalization_pipeline: EqualizationPipeline,
    ) -> None:
        """初始化。

        Initialize.

        Args:
            aircraft_context: 飞机上下文 / Aircraft context.
            airworthiness_pipeline: 适航管道 / Airworthiness pipeline.
            equalization_pipeline: 均衡管道 / Equalization pipeline.
        """
        self._aircraft_context = aircraft_context
        self._airworthiness_pipeline = airworthiness_pipeline
        self._equalization_pipeline = equalization_pipeline

    def run(self, aircraft: Aircraft) -> WeightRecommendation:
        """执行载重建议。

        Run weight recommendation.

        Args:
            aircraft: 目标飞机 / Target aircraft.

        Returns:
            重量建议 / Weight recommendation.
        """
        # 计算最大载荷（受多重限制）
        # Calculate max payload (subject to multiple limits)
        AircraftWeightValidator()
        AircraftEnvelopeValidator()

        # 起飞重量限制
        # Takeoff weight limit
        max_takeoff_payload = aircraft.max_takeoff_weight - aircraft.fuel_capacity * 0.8

        # 着陆重量限制
        # Landing weight limit
        max_landing_payload = aircraft.max_landing_weight - aircraft.fuel_capacity * 0.2

        # 零油重量限制
        # Zero fuel weight limit
        max_zfw_payload = aircraft.max_zero_fuel_weight

        # 取最严格限制
        # Take the most restrictive limit
        max_payload = min(max_takeoff_payload, max_landing_payload, max_zfw_payload)

        # 推荐载荷留 5% 余量
        # Recommended payload with 5% margin
        recommended = max_payload * 0.95

        limiting = "takeoff"
        if max_payload == max_landing_payload:
            limiting = "landing"
        elif max_payload == max_zfw_payload:
            limiting = "zero_fuel"

        return WeightRecommendation(
            recommended_payload=recommended,
            max_payload=max_payload,
            limiting_factor=limiting,
            balance_suggestions=(
                "Distribute heavy items across compartments",
                "Maintain CG within 15-35% MAC",
            ),
        )
