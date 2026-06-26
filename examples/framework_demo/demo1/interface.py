"""Demo1 Interface — 网络路由业务对外接口。"""

from __future__ import annotations

from dataclasses import dataclass

from .application import SSPApplication, SSPSolution
from .bandwidth_context.aggregation import Edge, Node
from .bandwidth_context.bandwidth_context import BandwidthContext
from .route_context.model.graph import Graph
from .route_context.model.service import Service
from .route_context.route_context import RouteContext


@dataclass
class Demo1Interface:
    """Demo1 外部接口，封装 SSP 求解流程。"""

    def create_and_solve(
        self,
        nodes: list[str],
        edges: list[tuple[str, str, str, float]],
        services: list[tuple[str, str, str, float]],
    ) -> SSPSolution:
        """创建网络并求解 SSP。

        Args:
            nodes: 节点 ID 列表
            edges: (edge_id, source, target, capacity) 列表
            services: (service_id, source, target, demand) 列表

        Returns:
            SSPSolution 求解结果
        """
        bw_ctx = BandwidthContext()
        for edge_id, src, tgt, cap in edges:
            bw_ctx = bw_ctx.register_edge(
                Edge(edge_id=edge_id, source=src, target=tgt, capacity=cap)
            )
        for node_id in nodes:
            bw_ctx = bw_ctx.register_node(
                Node(node_id=node_id, max_bandwidth=float("inf"))
            )

        route_ctx = RouteContext()
        graph = Graph(nodes=tuple(nodes), edges=tuple())
        route_ctx = route_ctx.register_graph(graph)
        for sid, src, tgt, demand in services:
            route_ctx = route_ctx.register_service(Service(sid, src, tgt, demand))

        app = SSPApplication(
            bandwidth_context=bw_ctx,
            route_context=route_ctx,
        )
        return app.solve()
