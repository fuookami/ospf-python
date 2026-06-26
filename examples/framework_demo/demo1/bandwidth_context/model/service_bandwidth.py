"""Service bandwidth model — 服务带宽需求。"""

from dataclasses import dataclass


@dataclass
class ServiceBandwidth:
    """Service bandwidth requirement."""

    service_id: str
    source: str
    target: str
    demand: float
    priority: int = 0
