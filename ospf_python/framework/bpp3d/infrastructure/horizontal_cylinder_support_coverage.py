"""水平圆柱体支撑覆盖 / Horizontal cylinder support coverage.

计算水平放置圆柱体的支撑面覆盖面积。
Calculates support surface coverage for horizontally
placed cylinders.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HorizontalCylinderSupportCoverage:
    """水平圆柱体支撑覆盖。

    描述水平放置圆柱体在容器底面上的投影覆盖。
    Describes the projection coverage of a horizontally
    placed cylinder on the container base surface.

    Attributes:
        radius: 圆柱半径 / Cylinder radius.
        length: 圆柱长度（水平方向）/ Cylinder length (horizontal).
        coverage_area: 投影覆盖面积 / Projection coverage area.
    """

    radius: float
    """圆柱半径 / Cylinder radius."""

    length: float
    """圆柱长度（水平方向）/ Cylinder length (horizontal)."""

    coverage_area: float
    """投影覆盖面积 / Projection coverage area."""

    @staticmethod
    def create(
        *,
        radius: float,
        length: float,
    ) -> HorizontalCylinderSupportCoverage:
        """创建支撑覆盖 / Create support coverage.

        Args:
            radius: 圆柱半径 / Cylinder radius.
            length: 圆柱长度 / Cylinder length.

        Returns:
            水平圆柱体支撑覆盖实例 /
            HorizontalCylinderSupportCoverage instance.
        """
        coverage = 2.0 * radius * length
        return HorizontalCylinderSupportCoverage(
            radius=radius,
            length=length,
            coverage_area=coverage,
        )

    @property
    def width(self) -> float:
        """投影宽度 / Projection width.

        Returns:
            2 倍半径 / 2 times radius.
        """
        return 2.0 * self.radius
