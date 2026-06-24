"""连续半径模型组件 / Continuous radius model component.

BPP3D 中圆柱体连续半径的模型组件。
Continuous radius model component for cylinders in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContinuousRadiusModelComponent:
    """连续半径模型组件。

    描述圆柱体物品在优化模型中的半径变量组件。
    Describes the radius variable component for
    cylinder items in the optimization model.

    Attributes:
        radius_lower: 半径下界 / Radius lower bound.
        radius_upper: 半径上界 / Radius upper bound.
        is_integer: 是否为整数变量 /
            Whether radius is integer variable.
    """

    radius_lower: float
    """半径下界 / Radius lower bound."""

    radius_upper: float
    """半径上界 / Radius upper bound."""

    is_integer: bool = False
    """是否为整数变量 / Whether integer variable."""

    @staticmethod
    def create(
        *,
        radius_lower: float,
        radius_upper: float,
        is_integer: bool = False,
    ) -> ContinuousRadiusModelComponent:
        """创建半径模型组件 / Create radius model component.

        Args:
            radius_lower: 半径下界 / Radius lower bound.
            radius_upper: 半径上界 / Radius upper bound.
            is_integer: 是否整数，默认 False /
                Is integer, default False.

        Returns:
            半径模型组件 / Radius model component.
        """
        return ContinuousRadiusModelComponent(
            radius_lower=radius_lower,
            radius_upper=radius_upper,
            is_integer=is_integer,
        )

    @property
    def radius_range(self) -> float:
        """半径范围 / Radius range.

        Returns:
            上界减下界 / Upper minus lower.
        """
        return self.radius_upper - self.radius_lower
