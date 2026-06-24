"""层分配类型别名 / Layer assignment type aliases.

定义层分配模块使用的类型别名。
Defines type aliases used in the layer assignment module.
"""

from __future__ import annotations

from ospf_python.framework.bpp3d.domain.layer_assignment.model.capacity import (
    Capacity,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.model.load import (
    Load,
)

type LayerId = str
"""层标识 / Layer identifier."""

type ContainerId = str
"""容器标识 / Container identifier."""

type LayerIndex = int
"""层索引 / Layer index."""

type Quantity = int
"""数量 / Quantity."""

type CapacityMap = dict[ContainerId, Capacity]
"""容量映射 / Capacity map."""

type LoadMap = dict[LayerId, Load]
"""负载映射 / Load map."""
