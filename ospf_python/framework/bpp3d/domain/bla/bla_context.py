"""BLA 上下文 / BLA context.

管理自底向上左对齐算法的运行时上下文。
Manages the runtime context for the bottom-up left-justified
algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BLAContext:
    """BLA 上下文 / BLA context.

    持有 BLA 算法运行所需的状态和配置。
    Holds state and configuration required by the BLA algorithm.

    Attributes:
        container_width: 容器宽度 / The container width.
        container_height: 容器高度 / The container height.
        container_depth: 容器深度 / The container depth.
        items: 待装箱物品列表 / The list of items to pack.
        max_iterations: 最大迭代次数 / Maximum iterations.
    """

    container_width: float = 0.0
    container_height: float = 0.0
    container_depth: float = 0.0
    items: tuple[object, ...] = field(
        default_factory=tuple,
    )
    max_iterations: int = 1000
