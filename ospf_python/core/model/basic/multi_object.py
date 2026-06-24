"""多目标包装器 / Multi-objective wrapper.

将多个目标函数组合为一个可管理的结构。
Combines multiple objective functions into a single
manageable structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MultiObject:
    """多目标包装器 / Multi-objective wrapper.

    用于多目标优化场景，将多个目标函数及其权重组合在一起。
    Used in multi-objective optimization scenarios to group
    multiple objective functions with their weights.

    Attributes:
        objectives: 目标函数列表 / List of objective functions.
        weights: 目标权重列表 / List of objective weights.
    """

    objectives: tuple[object, ...] = field(
        default_factory=tuple,
    )
    weights: tuple[float, ...] = field(
        default_factory=tuple,
    )
