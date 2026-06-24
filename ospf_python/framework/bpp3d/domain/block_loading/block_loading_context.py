"""块装载上下文 / Block loading context.

管理块装载算法的运行时上下文。
Manages the runtime context for block loading algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BlockLoadingContext:
    """块装载上下文 / Block loading context.

    持有块装载算法运行所需的状态和配置。
    Holds state and configuration required by block loading
    algorithms.

    Attributes:
        container_width: 容器宽度 / The container width.
        container_height: 容器高度 / The container height.
        container_depth: 容器深度 / The container depth.
        blocks: 待装载块列表 / The list of blocks to load.
        max_depth: 最大搜索深度 / Maximum search depth.
    """

    container_width: float = 0.0
    container_height: float = 0.0
    container_depth: float = 0.0
    blocks: tuple[object, ...] = field(
        default_factory=tuple,
    )
    max_depth: int = 100
