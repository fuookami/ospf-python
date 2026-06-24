"""影子价格 / Shadow price.

定义约束的影子价格数据结构。
Defines the data structure for constraint shadow prices.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShadowPrice:
    """影子价格 / Shadow price.

    表示约束的影子价格（对偶值），反映约束右端项
    变化一单位时目标函数的变化量。
    Represents the shadow price (dual value) of a constraint,
    reflecting the change in objective when the constraint
    RHS changes by one unit.

    Attributes:
        constraint_name: 约束名称 / The constraint name.
        value: 影子价格值 / The shadow price value.
    """

    constraint_name: str
    value: float
