"""最短路径服务 / Shortest path service.

实现 Dijkstra 最短路径算法。
Implements Dijkstra's shortest path algorithm.
"""

from __future__ import annotations

import heapq
from collections import defaultdict
from typing import TYPE_CHECKING

from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ospf_python.framework.network_scheduling.domain.edge.model.edge import (
        Edge,
    )
    from ospf_python.framework.network_scheduling.domain.node.model.node import (
        Node,
    )


class ShortestPath:
    """最短路径服务 / Shortest path service.

    提供基于 Dijkstra 算法的最短路径查询。
    Provides shortest path queries based on
    Dijkstra's algorithm.

    本类为无状态服务，所有方法均为静态方法。
    This is a stateless service; all methods are static.
    """

    @staticmethod
    def dijkstra(
        nodes: Sequence[Node],
        edges: Sequence[Edge],
        source_key: str,
        sink_key: str,
    ) -> Result[tuple[str, ...], str, Err[str]]:
        """Dijkstra 最短路径算法 / Dijkstra's shortest path algorithm.

        从 source_key 到 sink_key 寻找代价最小的路径。
        Finds the least-cost path from source_key to sink_key.

        使用邻接表和 heapq 优先队列实现。
        Implemented using an adjacency list and heapq
        priority queue.

        Args:
            nodes: 网络中的所有节点 / All nodes in the network.
            edges: 网络中的所有边 / All edges in the network.
            source_key: 源节点标识 / Source node identifier.
            sink_key: 汇节点标识 / Sink node identifier.

        Returns:
            成功时返回节点键序列（从源到汇），失败时返回错误。
            On success, a tuple of node keys from source to sink.
            On failure, an error describing what went wrong.
        """
        node_keys = {n.node_key for n in nodes}

        if source_key not in node_keys:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(f"源节点不存在 / Source node not found: {source_key}"),
                )
            )

        if sink_key not in node_keys:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(f"汇节点不存在 / Sink node not found: {sink_key}"),
                )
            )

        # 构建邻接表 / Build adjacency list
        adjacency: dict[str, list[tuple[float, str, str]]] = defaultdict(list)
        for edge in edges:
            adjacency[edge.from_node_key].append(
                (edge.cost, edge.to_node_key, edge.edge_key)
            )

        # Dijkstra 核心 / Dijkstra core
        dist: dict[str, float] = {}
        prev: dict[str, str | None] = {}
        visited: set[str] = set()

        # 初始化 / Initialize
        for nk in node_keys:
            dist[nk] = float("inf")
            prev[nk] = None
        dist[source_key] = 0.0

        # 优先队列: (累计代价, 节点键) /
        # Priority queue: (cumulative cost, node key)
        heap: list[tuple[float, str]] = [(0.0, source_key)]

        while heap:
            current_cost, current_key = heapq.heappop(heap)

            if current_key in visited:
                continue
            visited.add(current_key)

            # 到达汇节点 / Reached sink
            if current_key == sink_key:
                break

            for edge_cost, neighbor_key, _ in adjacency.get(current_key, []):
                if neighbor_key in visited:
                    continue
                new_cost = current_cost + edge_cost
                if new_cost < dist[neighbor_key]:
                    dist[neighbor_key] = new_cost
                    prev[neighbor_key] = current_key
                    heapq.heappush(heap, (new_cost, neighbor_key))

        # 检查可达性 / Check reachability
        if dist.get(sink_key, float("inf")) == float("inf"):
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(
                        f"从 {source_key} 到 {sink_key} "
                        f"无可达路径 / "
                        f"No path from {source_key} "
                        f"to {sink_key}"
                    ),
                )
            )

        # 回溯路径 / Backtrack path
        path: list[str] = []
        current: str | None = sink_key
        while current is not None:
            path.append(current)
            current = prev[current]
        path.reverse()

        return Ok(tuple(path))
