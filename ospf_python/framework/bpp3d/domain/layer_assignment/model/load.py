"""负载数据结构 / Load data structure.

表示层的负载信息。
Represents load information of a layer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Load:
    """负载 / Load.

    描述层在各维度上的负载。
    Describes the load of a layer along each dimension.

    Attributes:
        width: 宽度负载 / The width load.
        height: 高度负载 / The height load.
        depth: 深度负载 / The depth load.
        weight: 重量负载 / The weight load.
    """

    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0
    weight: float = 0.0
