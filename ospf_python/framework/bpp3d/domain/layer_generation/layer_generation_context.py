"""层生成上下文 / Layer generation context.

管理层生成算法的运行时上下文。
Manages the runtime context for layer generation algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LayerGenerationContext:
    """层生成上下文 / Layer generation context.

    持有层生成算法运行所需的状态和配置。
    Holds state and configuration required by layer generation
    algorithms.

    Attributes:
        items: 物品列表 / The list of items.
        container_width: 容器宽度 / The container width.
        container_depth: 容器深度 / The container depth.
        max_layers: 最大层数 / Maximum number of layers.
        candidates: 候选层列表 / The list of candidate layers.
    """

    items: tuple[object, ...] = field(
        default_factory=tuple,
    )
    container_width: float = 0.0
    container_depth: float = 0.0
    max_layers: int = 100
    candidates: tuple[object, ...] = field(
        default_factory=tuple,
    )
