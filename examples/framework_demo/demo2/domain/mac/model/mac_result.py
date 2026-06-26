"""平均气动弦长计算结果 / Mean Aerodynamic Chord result.

定义 MAC 计算结果的数据结构。
Defines the data structure for MAC calculation results.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MACResult:
    """平均气动弦长计算结果 / Mean Aerodynamic Chord result.

    描述机翼平均气动弦长的计算值及其前后缘站位。
    Describes the computed mean aerodynamic chord value
    and the leading/trailing edge station positions.

    Attributes:
        mac_value: 平均气动弦长 (m) / MAC value (m).
        leading_edge: 前缘站位 (m) / Leading edge station (m).
        trailing_edge: 后缘站位 (m) / Trailing edge station (m).
        station: MAC 中点站位 (m) / MAC midpoint station (m).
    """

    mac_value: float
    """平均气动弦长 (m) / MAC value (m)."""

    leading_edge: float
    """前缘站位 (m) / Leading edge station (m)."""

    trailing_edge: float
    """后缘站位 (m) / Trailing edge station (m)."""

    station: float
    """MAC 中点站位 (m) / MAC midpoint station (m)."""

    @staticmethod
    def create(
        *,
        mac_value: float,
        leading_edge: float,
        trailing_edge: float,
        station: float,
    ) -> MACResult:
        """创建 MAC 结果实例 / Create MAC result instance.

        Args:
            mac_value: 平均气动弦长 / MAC value.
            leading_edge: 前缘站位 / Leading edge station.
            trailing_edge: 后缘站位 / Trailing edge station.
            station: MAC 中点站位 / MAC midpoint station.

        Returns:
            MAC 结果实例 / MAC result instance.
        """
        return MACResult(
            mac_value=mac_value,
            leading_edge=leading_edge,
            trailing_edge=trailing_edge,
            station=station,
        )

    @property
    def chord_length(self) -> float:
        """弦长（前后缘距离）/ Chord length (LE to TE distance).

        Returns:
            前后缘站位差 (m) / Difference between TE and LE (m).
        """
        return self.trailing_edge - self.leading_edge

    def contains_station(self, fuselage_station: float) -> bool:
        """判断站位是否在 MAC 前后缘范围内。

        Check whether a station lies within the MAC
        leading/trailing edge range.

        Args:
            fuselage_station: 机身站位 (m) / Fuselage station (m).

        Returns:
            站位在 MAC 范围内则返回 True。
            True if station is within MAC range.
        """
        return self.leading_edge <= fuselage_station <= self.trailing_edge
