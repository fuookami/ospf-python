"""层分配上下文 / Layer assignment context.

管理层分配算法的运行时上下文。
Manages the runtime context for layer assignment algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LayerAssignmentContext:
    """层分配上下文 / Layer assignment context.

    持有层分配算法运行所需的状态和配置。
    Holds state and configuration required by layer assignment
    algorithms.

    Attributes:
        layers: 可用层列表 / The list of available layers.
        containers: 可用容器列表 / The list of available
            containers.
        demand: 需求量 / The demand quantity.
        max_layers_per_bin: 每箱最大层数 / Maximum layers
            per bin.
    """

    layers: tuple[object, ...] = field(
        default_factory=tuple,
    )
    containers: tuple[object, ...] = field(
        default_factory=tuple,
    )
    demand: int = 0
    max_layers_per_bin: int = 100
