"""MAC 上下文 / MAC context.

封装 MAC 计算的运行时状态，提供注册和查找功能。
Encapsulates MAC calculation runtime state with
registration and lookup capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.mac.model.mac_aggregation import (
    MACAggregation,
)
from examples.framework_demo.demo2.domain.mac.model.mac_position import (
    MACPosition,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.mac.model.mac_result import (
        MACResult,
    )

    pass


@dataclass(frozen=True)
class MACContext:
    """MAC 上下文 / MAC context.

    持有当前机型的 MAC 计算结果和当前位置信息，
    提供注册新结果和查找位置的方法。
    Holds the current aircraft type's MAC results and
    position information, with methods to register new
    results and look up positions.

    Attributes:
        aggregation: MAC 结果聚合 / MAC result aggregation.
        current_position: 当前 MAC 位置 / Current MAC position.
        reference_station: 参考站位 (m) / Reference station (m).
    """

    aggregation: MACAggregation
    """MAC 结果聚合 / MAC result aggregation."""

    current_position: MACPosition
    """当前 MAC 位置 / Current MAC position."""

    reference_station: float
    """参考站位 (m)，通常为机翼前缘根弦站位。
    Reference station (m), typically the wing root
    leading edge station."""

    @staticmethod
    def create(
        *,
        aggregation: MACAggregation,
        current_position: MACPosition,
        reference_station: float = 0.0,
    ) -> MACContext:
        """创建 MAC 上下文 / Create MAC context.

        Args:
            aggregation: MAC 结果聚合 / MAC result aggregation.
            current_position: 当前 MAC 位置 / Current MAC position.
            reference_station: 参考站位，默认 0.0 /
                Reference station, default 0.0.

        Returns:
            MAC 上下文实例 / MAC context instance.
        """
        return MACContext(
            aggregation=aggregation,
            current_position=current_position,
            reference_station=reference_station,
        )

    @staticmethod
    def empty(*, aircraft_type: str) -> MACContext:
        """创建空上下文 / Create empty context.

        Args:
            aircraft_type: 机型代码 / Aircraft type code.

        Returns:
            空的 MAC 上下文 / Empty MAC context.
        """
        return MACContext(
            aggregation=MACAggregation.empty(aircraft_type=aircraft_type),
            current_position=MACPosition.create(
                fuselage_station=0.0,
                percent_mac=0.0,
                cg_arm=0.0,
            ),
            reference_station=0.0,
        )

    def register_result(self, result: MACResult) -> MACContext:
        """注册新的 MAC 结果（返回新上下文）。

        Register a new MAC result (returns new context).

        Args:
            result: 待注册的 MAC 结果 / MAC result to register.

        Returns:
            包含新结果的新上下文 / New context with added result.
        """
        return MACContext(
            aggregation=self.aggregation.add(result),
            current_position=self.current_position,
            reference_station=self.reference_station,
        )

    def with_position(self, position: MACPosition) -> MACContext:
        """更新当前 MAC 位置（返回新上下文）。

        Update current MAC position (returns new context).

        Args:
            position: 新 MAC 位置 / New MAC position.

        Returns:
            更新后的新上下文 / New updated context.
        """
        return MACContext(
            aggregation=self.aggregation,
            current_position=position,
            reference_station=self.reference_station,
        )

    def lookup_by_station(self, fuselage_station: float) -> tuple[MACResult, ...]:
        """按站位查找 MAC 结果 / Lookup MAC results by station.

        Args:
            fuselage_station: 机身站位 (m) / Fuselage station (m).

        Returns:
            包含该站位的 MAC 结果元组 /
            Tuple of MAC results containing the station.
        """
        return self.aggregation.containing_station(fuselage_station)

    @property
    def has_results(self) -> bool:
        """是否有已注册的 MAC 结果。

        Whether there are registered MAC results.

        Returns:
            有结果时返回 True / True if results exist.
        """
        return not self.aggregation.is_empty

    @property
    def primary_mac(self) -> MACResult | None:
        """获取主 MAC 结果 / Get primary MAC result.

        Returns:
            主 MAC 结果或 None / Primary MAC result or None.
        """
        return self.aggregation.primary
