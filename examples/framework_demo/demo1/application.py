"""SSP Application — Shortest Service Path solver.

对齐 Kotlin Application.kt 184 行：用 framework context/solver
编排路由+带宽分配的 SSP 最短服务路径求解。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bandwidth_context.bandwidth_context import BandwidthContext
    from .route_context.route_context import RouteContext


@dataclass
class SSPSolution:
    """SSP 求解结果。"""

    routes: dict[str, list[str]] = field(default_factory=dict)
    total_cost: float = float("inf")
    feasible: bool = False
    bandwidth_used: dict[str, float] = field(default_factory=dict)


@dataclass
class SSPApplication:
    """Shortest Service Path solver.

    用 framework context/solver 编排路由+带宽分配。
    Aligns with Kotlin Application.kt (184 lines).
    """

    bandwidth_context: BandwidthContext
    route_context: RouteContext

    def solve(self) -> SSPSolution:
        """Solve SSP routing + bandwidth allocation."""
        graph = self.route_context.get_graph()
        services = self.route_context.get_services()
        edges = self.bandwidth_context.edges

        if not graph or not services:
            return SSPSolution(feasible=False)

        # Build edge cost/capacity lookup from bandwidth edges
        edge_map: dict[tuple[str, str], float] = {}
        capacity_map: dict[tuple[str, str], float] = {}
        node_set: set[str] = set()
        adj: dict[str, list[str]] = {}
        for e in edges:
            edge_map[(e.source, e.target)] = 1.0
            capacity_map[(e.source, e.target)] = e.capacity
            node_set.add(e.source)
            node_set.add(e.target)
            adj.setdefault(e.source, []).append(e.target)

        # Dijkstra-like SSP per service
        routes: dict[str, list[str]] = {}
        bandwidth_used: dict[str, float] = {}
        total_cost = 0.0

        for svc in services:
            path, cost = self._shortest_path(adj, svc.source, svc.target, edge_map)
            if path is None:
                return SSPSolution(feasible=False)

            # Check bandwidth constraint
            for i in range(len(path) - 1):
                edge_key = (path[i], path[i + 1])
                used = bandwidth_used.get(f"{edge_key}", 0.0)
                cap = capacity_map.get(edge_key, float("inf"))
                if used + svc.demand > cap:
                    return SSPSolution(feasible=False)

            # Record bandwidth usage
            for i in range(len(path) - 1):
                edge_key = (path[i], path[i + 1])
                key_str = f"{edge_key}"
                bandwidth_used[key_str] = bandwidth_used.get(key_str, 0.0) + svc.demand

            routes[svc.service_id] = path
            total_cost += cost * svc.demand

        return SSPSolution(
            routes=routes,
            total_cost=total_cost,
            feasible=True,
            bandwidth_used=bandwidth_used,
        )

    def _shortest_path(
        self,
        adj: dict[str, list[str]],
        source: str,
        target: str,
        edge_costs: dict[tuple[str, str], float],
    ) -> tuple[list[str] | None, float]:
        """Dijkstra shortest path."""
        import heapq

        dist: dict[str, float] = {source: 0.0}
        prev: dict[str, str | None] = {source: None}
        pq: list[tuple[float, str]] = [(0.0, source)]
        visited: set[str] = set()

        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)

            if u == target:
                path: list[str] = []
                node: str | None = target
                while node is not None:
                    path.append(node)
                    node = prev.get(node)
                path.reverse()
                return path, d

            for v in adj.get(u, []):
                edge_cost = edge_costs.get((u, v), 1.0)
                new_dist = d + edge_cost
                if v not in dist or new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heapq.heappush(pq, (new_dist, v))

        return None, float("inf")
