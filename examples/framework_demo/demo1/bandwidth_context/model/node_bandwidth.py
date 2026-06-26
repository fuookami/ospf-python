"""Node bandwidth model — 网络节点带宽。"""

from dataclasses import dataclass


@dataclass
class NodeBandwidth:
    """Node with bandwidth capacity."""

    node_id: str
    capacity: float
    demand: float = 0.0
