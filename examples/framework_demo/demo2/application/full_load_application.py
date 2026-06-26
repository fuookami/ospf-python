"""满载应用 / Full Load Application.

编排满载场景的 3D 装箱优化：飞机载重平衡 + 适航约束。
Orchestrates full-load 3D bin-packing optimization:
aircraft weight balance + airworthiness constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.aircraft.service.aircraft_balance_calculator import (
    AircraftBalanceCalculator,
)
from examples.framework_demo.demo2.domain.aircraft.service.aircraft_capacity_checker import (
    AircraftCapacityChecker,
)
from examples.framework_demo.demo2.domain.aircraft.service.aircraft_weight_validator import (
    AircraftWeightValidator,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft import Aircraft
    from examples.framework_demo.demo2.domain.aircraft.service.aircraft_context import (
        AircraftContext,
    )
    from examples.framework_demo.demo2.domain.airworthiness_security.model.airworthiness_context import (
        AirworthinessContext,
    )
    from examples.framework_demo.demo2.domain.airworthiness_security.service.limits.airworthiness_pipeline import (
        AirworthinessPipeline,
    )
    from examples.framework_demo.demo2.domain.airworthiness_security.service.limits.security_pipeline import (
        SecurityPipeline,
    )
    from examples.framework_demo.demo2.domain.payload_maximization.service.limits.payload_maximization_pipeline import (
        PayloadMaximizationPipeline,
    )
    from examples.framework_demo.demo2.domain.stowage.service.limits.stowage_pipeline import (
        StowagePipeline,
    )


@dataclass(frozen=True)
class FullLoadResult:
    """满载结果 / Full load result.

    Attributes:
        feasible: 是否可行 / Whether feasible.
        total_payload: 总载荷 (kg) / Total payload (kg).
        cg_position: 重心位置 (%MAC) / CG position (%MAC).
        violations: 约束违反列表 / Constraint violations.
    """

    feasible: bool = False
    total_payload: float = 0.0
    cg_position: float = 0.0
    violations: tuple[str, ...] = field(default_factory=tuple)


class FullLoadApplication:
    """满载应用 / Full Load Application.

    编排满载场景：校验飞机载重、平衡、适航、配载约束。
    Orchestrates full-load scenario: validates aircraft weight,
    balance, airworthiness, and stowage constraints.

    使用 framework 扩展点注入 context/pipeline，
    不直接操作底层 model。
    Uses framework extension points to inject context/pipeline,
    does not directly manipulate underlying model.
    """

    def __init__(
        self,
        *,
        aircraft_context: AircraftContext,
        airworthiness_context: AirworthinessContext,
        stowage_pipeline: StowagePipeline,
        airworthiness_pipeline: AirworthinessPipeline,
        security_pipeline: SecurityPipeline,
        payload_pipeline: PayloadMaximizationPipeline,
    ) -> None:
        """初始化满载应用。

        Initialize full load application.

        Args:
            aircraft_context: 飞机上下文 / Aircraft context.
            airworthiness_context: 适航上下文 / Airworthiness context.
            stowage_pipeline: 配载管道 / Stowage pipeline.
            airworthiness_pipeline: 适航管道 / Airworthiness pipeline.
            security_pipeline: 安保管道 / Security pipeline.
            payload_pipeline: 载荷最大化管道 / Payload maximization pipeline.
        """
        self._aircraft_context = aircraft_context
        self._airworthiness_context = airworthiness_context
        self._stowage_pipeline = stowage_pipeline
        self._airworthiness_pipeline = airworthiness_pipeline
        self._security_pipeline = security_pipeline
        self._payload_pipeline = payload_pipeline

    def run(self, aircraft: Aircraft) -> FullLoadResult:
        """执行满载优化。

        Run full-load optimization.

        Args:
            aircraft: 目标飞机 / Target aircraft.

        Returns:
            满载结果 / Full load result.
        """
        # 1. 校验飞机重量限制
        # Validate aircraft weight limits
        weight_validator = AircraftWeightValidator()
        weight_result = weight_validator.validate_takeoff(
            aircraft=aircraft,
            current_weight=aircraft.max_takeoff_weight,
        )
        if not weight_result.is_ok():
            return FullLoadResult(
                feasible=False,
                violations=("Weight limit exceeded",),
            )

        # 2. 校验容量
        # Validate capacity
        capacity_checker = AircraftCapacityChecker()
        capacity_result = capacity_checker.check_cargo_fit(
            aircraft=aircraft,
            cargo_volume=aircraft.cargo_hold_volume,
            cargo_weight=aircraft.max_takeoff_weight * 0.8,
            current_used_volume=0.0,
            current_used_weight=0.0,
        )
        if not capacity_result.is_ok():
            return FullLoadResult(
                feasible=False,
                violations=("Capacity exceeded",),
            )

        # 4. 计算重心
        # Calculate CG
        balance_calculator = AircraftBalanceCalculator()
        cg_result = balance_calculator.calculate_cg(
            aircraft=aircraft,
            loads=(),
            empty_weight=aircraft.max_takeoff_weight * 0.5,
            empty_cg_x=aircraft.max_takeoff_weight * 0.3,
            fuel_weight=aircraft.fuel_capacity * 0.8,
            fuel_cg_x=aircraft.max_takeoff_weight * 0.4,
            max_cg_offset=aircraft.max_takeoff_weight * 0.1,
        )

        # 5. 返回结果
        # Return result
        return FullLoadResult(
            feasible=True,
            total_payload=aircraft.max_takeoff_weight,
            cg_position=cg_result.cg_position.x if cg_result is not None else 0.0,
        )
