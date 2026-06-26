"""平均气动弦长计算器 / Mean Aerodynamic Chord calculator.

根据机翼几何参数计算平均气动弦长。
Computes the mean aerodynamic chord from wing geometry.
"""

from __future__ import annotations

from dataclasses import dataclass

from examples.framework_demo.demo2.domain.mac.model.mac_result import (
    MACResult,
)


@dataclass(frozen=True)
class WingGeometry:
    """机翼几何参数 / Wing geometry parameters.

    描述用于 MAC 计算的机翼基本几何参数。
    Describes the basic wing geometry parameters
    used for MAC calculation.

    Attributes:
        root_chord: 翼根弦长 (m) / Root chord length (m).
        tip_chord: 翼尖弦长 (m) / Tip chord length (m).
        span: 翼展 (m) / Wingspan (m).
        sweep_angle: 后掠角 (deg) / Sweep angle (deg).
        root_leading_edge_x: 翼根前缘站位 (m) /
            Root leading edge station (m).
    """

    root_chord: float
    """翼根弦长 (m) / Root chord length (m)."""

    tip_chord: float
    """翼尖弦长 (m) / Tip chord length (m)."""

    span: float
    """翼展 (m) / Wingspan (m)."""

    sweep_angle: float
    """后掠角 (deg) / Sweep angle (deg)."""

    root_leading_edge_x: float
    """翼根前缘站位 (m) / Root leading edge station (m)."""

    @staticmethod
    def create(
        *,
        root_chord: float,
        tip_chord: float,
        span: float,
        sweep_angle: float,
        root_leading_edge_x: float,
    ) -> WingGeometry:
        """创建机翼几何参数 / Create wing geometry.

        Args:
            root_chord: 翼根弦长 / Root chord length.
            tip_chord: 翼尖弦长 / Tip chord length.
            span: 翼展 / Wingspan.
            sweep_angle: 后掠角 / Sweep angle.
            root_leading_edge_x: 翼根前缘站位 /
                Root leading edge station.

        Returns:
            机翼几何参数实例 / Wing geometry instance.
        """
        return WingGeometry(
            root_chord=root_chord,
            tip_chord=tip_chord,
            span=span,
            sweep_angle=sweep_angle,
            root_leading_edge_x=root_leading_edge_x,
        )


class MACCalculator:
    """平均气动弦长计算器 / MAC calculator.

    根据机翼几何参数计算平均气动弦长 (MAC) 及其前后缘
    站位。MAC 的标准公式基于梯形机翼的面积矩积分。
    Computes the mean aerodynamic chord (MAC) and its
    leading/trailing edge stations from wing geometry.
    The standard MAC formula is based on the area-moment
    integral of a trapezoidal wing.
    """

    def calculate(self, geometry: WingGeometry) -> MACResult:
        """计算 MAC / Calculate MAC.

        使用标准梯形翼 MAC 公式：
            MAC = (2/3) * (Cr + Ct - Cr*Ct/(Cr+Ct))
        其中 Cr 为翼根弦长，Ct 为翼尖弦长。

        Uses the standard trapezoidal wing MAC formula:
            MAC = (2/3) * (Cr + Ct - Cr*Ct/(Cr+Ct))
        where Cr is root chord and Ct is tip chord.

        Args:
            geometry: 机翼几何参数 / Wing geometry parameters.

        Returns:
            MAC 计算结果 / MAC calculation result.
        """
        cr = geometry.root_chord
        ct = geometry.tip_chord
        span = geometry.span
        sweep = geometry.sweep_angle

        import math

        sweep_rad = math.radians(sweep)

        # MAC 弦长计算 / MAC chord length calculation
        if cr + ct == 0.0:
            mac_value = 0.0
        else:
            mac_value = (2.0 / 3.0) * (cr + ct - (cr * ct) / (cr + ct))

        # MAC 展向位置 (距翼根的距离) /
        # MAC spanwise position (distance from root)
        y_mac = 0.0 if cr + ct == 0.0 else span / 6.0 * (cr + 2.0 * ct) / (cr + ct)

        # MAC 前缘站位，考虑后掠角 /
        # MAC leading edge station, considering sweep
        le_offset = y_mac * math.tan(sweep_rad)
        leading_edge = geometry.root_leading_edge_x + le_offset

        # MAC 后缘站位 / MAC trailing edge station
        trailing_edge = leading_edge + mac_value

        # MAC 中点站位 / MAC midpoint station
        station = (leading_edge + trailing_edge) / 2.0

        return MACResult.create(
            mac_value=mac_value,
            leading_edge=leading_edge,
            trailing_edge=trailing_edge,
            station=station,
        )

    def calculate_mac_fraction(
        self,
        *,
        mac_result: MACResult,
        fuselage_station: float,
    ) -> float:
        """计算指定站位的 MAC 百分比。

        Calculate the percent MAC at a given station.

        公式: %MAC = (FS - LE) / MAC * 100
        Formula: %MAC = (FS - LE) / MAC * 100

        Args:
            mac_result: MAC 计算结果 / MAC result.
            fuselage_station: 机身站位 (m) / Fuselage station (m).

        Returns:
            MAC 百分比 (%%) / Percent MAC (%%).
        """
        if mac_result.mac_value == 0.0:
            return 0.0
        return (
            (fuselage_station - mac_result.leading_edge) / mac_result.mac_value
        ) * 100.0
