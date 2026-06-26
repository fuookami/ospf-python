"""CG 到 MAC 转换器 / CG to MAC converter.

将重心位置转换为 %MAC 表示。
Converts CG position to percent MAC representation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from examples.framework_demo.demo2.domain.mac.model.mac_position import (
    MACPosition,
)

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.mac.model.mac_result import (
        MACResult,
    )


@dataclass(frozen=True)
class CGToMACInput:
    """CG 到 MAC 转换输入 / CG to MAC conversion input.

    描述转换所需的输入参数。
    Describes the input parameters for conversion.

    Attributes:
        cg_station: 重心站位 (m) / CG station (m).
        mac_result: MAC 计算结果 / MAC calculation result.
        datum_station: 基准站位 (m) / Datum station (m).
    """

    cg_station: float
    """重心站位 (m) / CG station (m)."""

    mac_result: MACResult
    """MAC 计算结果 / MAC calculation result."""

    datum_station: float
    """基准站位 (m)，用于计算臂长。/ Datum station (m)
    used for arm calculation."""


class CGToMACConverter:
    """CG 到 MAC 转换器 / CG to MAC converter.

    将机身站位形式的重心位置转换为以 %MAC 表示的位置，
    并计算相对于基准站位的臂长。
    Converts the CG position from fuselage station form to
    percent MAC representation, and computes the arm length
    relative to the datum station.
    """

    def convert(self, cg_input: CGToMACInput) -> MACPosition:
        """执行转换 / Perform conversion.

        公式:
            %MAC = (CG_station - LE) / MAC * 100
            arm  = CG_station - datum_station

        Formulas:
            %MAC = (CG_station - LE) / MAC * 100
            arm  = CG_station - datum_station

        Args:
            cg_input: 转换输入 / Conversion input.

        Returns:
            MAC 位置实例 / MAC position instance.
        """
        mac = cg_input.mac_result.mac_value
        le = cg_input.mac_result.leading_edge

        percent_mac = 0.0 if mac == 0.0 else (cg_input.cg_station - le) / mac * 100.0

        cg_arm = cg_input.cg_station - cg_input.datum_station

        return MACPosition.create(
            fuselage_station=cg_input.cg_station,
            percent_mac=percent_mac,
            cg_arm=cg_arm,
        )

    def convert_station_to_mac(
        self,
        *,
        fuselage_station: float,
        mac_result: MACResult,
    ) -> float:
        """仅计算 %MAC 值 / Calculate percent MAC value only.

        不创建完整的 MACPosition 对象。
        Does not create a full MACPosition object.

        Args:
            fuselage_station: 机身站位 (m) / Fuselage station (m).
            mac_result: MAC 计算结果 / MAC result.

        Returns:
            MAC 百分比 (%%) / Percent MAC (%%).
        """
        if mac_result.mac_value == 0.0:
            return 0.0
        return (
            (fuselage_station - mac_result.leading_edge) / mac_result.mac_value
        ) * 100.0

    def mac_to_station(
        self,
        *,
        percent_mac: float,
        mac_result: MACResult,
    ) -> float:
        """将 %MAC 转换回机身站位 / Convert percent MAC back to station.

        公式: FS = LE + %MAC / 100 * MAC
        Formula: FS = LE + %MAC / 100 * MAC

        Args:
            percent_mac: MAC 百分比 (%%) / Percent MAC (%%).
            mac_result: MAC 计算结果 / MAC result.

        Returns:
            机身站位 (m) / Fuselage station (m).
        """
        return mac_result.leading_edge + (percent_mac / 100.0) * mac_result.mac_value

    def batch_convert(
        self,
        *,
        stations: tuple[float, ...],
        mac_result: MACResult,
        datum_station: float = 0.0,
    ) -> tuple[MACPosition, ...]:
        """批量转换 / Batch conversion.

        Args:
            stations: 机身站位元组 / Tuple of fuselage stations.
            mac_result: MAC 计算结果 / MAC result.
            datum_station: 基准站位 / Datum station.

        Returns:
            MAC 位置元组 / Tuple of MAC positions.
        """
        return tuple(
            self.convert(
                CGToMACInput(
                    cg_station=station,
                    mac_result=mac_result,
                    datum_station=datum_station,
                )
            )
            for station in stations
        )
