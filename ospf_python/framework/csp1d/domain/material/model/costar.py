"""CSP1D 协切产品模型 / CSP1D co-cut product model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Costar:
    """协切产品关系定义 / Co-cut product relationship.

    描述在同一切割方案中可同时产出的两个产品之间的兼容关系。
    Describes the compatibility relationship between two
    products that can be co-produced in the same cutting plan.

    Attributes:
        left: 左侧产品名称 / Left product name.
        right: 右侧产品名称 / Right product name.
        compatible: 是否兼容 / Whether compatible for co-cutting.
    """

    left: str
    right: str
    compatible: bool
