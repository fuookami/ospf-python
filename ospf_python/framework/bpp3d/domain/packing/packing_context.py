"""装箱上下文 / Packing context.

管理装箱算法的运行时上下文。
Manages the runtime context for packing algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PackingContext:
    """装箱上下文 / Packing context.

    持有装箱算法运行所需的状态和配置。
    Holds state and configuration required by packing algorithms.

    Attributes:
        container_width: 容器宽度 / The container width.
        container_height: 容器高度 / The container height.
        container_depth: 容器深度 / The container depth.
        items: 待装箱物品列表 / The list of items to pack.
        max_solutions: 最大方案数 / Maximum number of solutions.
    """

    container_width: float = 0.0
    container_height: float = 0.0
    container_depth: float = 0.0
    items: tuple[object, ...] = field(
        default_factory=tuple,
    )
    max_solutions: int = 1
