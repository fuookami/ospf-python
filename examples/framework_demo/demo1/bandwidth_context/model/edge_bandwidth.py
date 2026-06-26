"""Edge bandwidth model — 网络边带宽。"""

from dataclasses import dataclass


@dataclass
class EdgeBandwidth:
    """Edge with bandwidth capacity."""

    edge_id: str
    source: str
    target: str
    capacity: float
    cost: float = 0.0
