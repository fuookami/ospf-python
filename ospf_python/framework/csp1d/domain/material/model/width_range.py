"""CSP1D 宽度范围模型 / CSP1D width range model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WidthRange:
    """宽度取值范围 / Width value range.

    描述材料或产品宽度的上下界。
    Describes the upper and lower bounds of
    material or product width.

    Attributes:
        min_width: 最小宽度 / Minimum width.
        max_width: 最大宽度 / Maximum width.
    """

    min_width: float
    max_width: float
