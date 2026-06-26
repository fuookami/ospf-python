"""MAC 位置定义 / MAC position definition.

定义重心相对于 MAC 的位置数据结构。
Defines the data structure for CG position relative to MAC.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MACPosition:
    """MAC 位置 / MAC position.

    描述重心相对于平均气动弦长的位置，包括机身站位、
    占 MAC 百分比和 CG 臂长。
    Describes the CG position relative to the mean
    aerodynamic chord, including fuselage station,
    percent MAC, and CG arm.

    Attributes:
        fuselage_station: 机身站位 (m) / Fuselage station (m).
        percent_mac: 占 MAC 百分比 (%) / Percent MAC (%).
        cg_arm: 重心臂长 (m) / CG arm length (m).
    """

    fuselage_station: float
    """机身站位 (m) / Fuselage station (m)."""

    percent_mac: float
    """占 MAC 百分比 (%) / Percent MAC (%)."""

    cg_arm: float
    """重心臂长 (m) / CG arm length (m)."""

    @staticmethod
    def create(
        *,
        fuselage_station: float,
        percent_mac: float,
        cg_arm: float,
    ) -> MACPosition:
        """创建 MAC 位置实例 / Create MAC position instance.

        Args:
            fuselage_station: 机身站位 / Fuselage station.
            percent_mac: 占 MAC 百分比 / Percent MAC.
            cg_arm: 重心臂长 / CG arm length.

        Returns:
            MAC 位置实例 / MAC position instance.
        """
        return MACPosition(
            fuselage_station=fuselage_station,
            percent_mac=percent_mac,
            cg_arm=cg_arm,
        )

    @property
    def is_forward(self) -> bool:
        """重心是否偏前 / Whether CG is forward.

        百分比低于 25%% 通常视为偏前。
        Below 25%% MAC is generally considered forward.

        Returns:
            percent_mac < 25 时返回 True。
            True if percent_mac < 25.
        """
        return self.percent_mac < 25.0

    @property
    def is_aft(self) -> bool:
        """重心是否偏后 / Whether CG is aft.

        百分比高于 33%% 通常视为偏后。
        Above 33%% MAC is generally considered aft.

        Returns:
            percent_mac > 33 时返回 True。
            True if percent_mac > 33.
        """
        return self.percent_mac > 33.0

    def with_fuselage_station(self, fuselage_station: float) -> MACPosition:
        """更新机身站位（返回新实例）。

        Update fuselage station (returns new instance).

        Args:
            fuselage_station: 新机身站位 / New fuselage station.

        Returns:
            更新后的新实例 / New updated instance.
        """
        return MACPosition(
            fuselage_station=fuselage_station,
            percent_mac=self.percent_mac,
            cg_arm=self.cg_arm,
        )
