"""CSP1D 切割方案约束集合。

定义切割方案生成时使用的各类约束条件。
Constraints collection for cutting plan generation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Constraints:
    """切割方案约束集合 / Cutting plan constraints.

    汇总生成切割方案时需要满足的所有约束条件。
    Aggregates all constraint conditions that must be
    satisfied during cutting plan generation.

    Attributes:
        max_knife_count: 最大刀数 / Maximum knife count.
        min_length: 最小长度 / Minimum length.
        max_length: 最大长度 / Maximum length.
        min_width: 最小宽度 / Minimum width.
        max_width: 最大宽度 / Maximum width.
        allow_waste: 是否允许余料 / Whether waste is allowed.
        precision: 数值精度 / Numerical precision.
    """

    max_knife_count: int = 0
    """最大刀数 / Maximum knife count."""

    min_length: float = 0.0
    """最小长度 / Minimum length."""

    max_length: float = float("inf")
    """最大长度 / Maximum length."""

    min_width: float = 0.0
    """最小宽度 / Minimum width."""

    max_width: float = float("inf")
    """最大宽度 / Maximum width."""

    allow_waste: bool = True
    """是否允许余料 / Whether waste is allowed."""

    precision: float = 1e-8
    """数值精度 / Numerical precision."""
