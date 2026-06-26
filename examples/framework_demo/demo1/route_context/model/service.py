"""Service model — 网络服务。

定义需要在网络中路由的服务需求。
Defines service demands that need to be routed through the network.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Service:
    """网络服务 / Network service.

    表示一条需要从源节点路由到目标节点的服务流，
    包含带宽需求量。
    Represents a service flow that needs to be routed
    from source to target node, with a bandwidth demand.

    Attributes:
        service_id: 服务标识 / Service identifier.
        source: 源节点 / Source node.
        target: 目标节点 / Target node.
        demand: 带宽需求量 / Bandwidth demand.
    """

    service_id: str
    source: str
    target: str
    demand: float
