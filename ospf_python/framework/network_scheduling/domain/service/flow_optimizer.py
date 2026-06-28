"""流优化服务 / Flow optimizer service.

实现基于贪心最短路径的最小代价流启发式算法。
Implements a greedy shortest-path based min-cost flow
heuristic algorithm.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from ospf_python.framework.network_scheduling.domain.flow.model.flow import (
    Flow,
)
from ospf_python.framework.network_scheduling.domain.service.shortest_path import (
    ShortestPath,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ospf_python.framework.network_scheduling.domain.edge.model.edge import (
        Edge,
    )
    from ospf_python.framework.network_scheduling.domain.flow.model.demand import (
        Demand,
    )
    from ospf_python.framework.network_scheduling.domain.node.model.node import (
        Node,
    )


class FlowOptimizer:
    """流优化服务 / Flow optimizer service.

    使用贪心最短路径方法进行最小代价流分配。
    Uses a greedy shortest-path approach for min-cost
    flow allocation.

    对每个需求，找到最短路径后推送流量，然后更新残余容量。
    For each demand, finds the shortest path, pushes flow,
    then updates residual capacities.

    本类为无状态服务，所有方法均为静态方法。
    This is a stateless service; all methods are static.
    """

    @staticmethod
    def optimize(
        nodes: Sequence[Node],
        edges: Sequence[Edge],
        demands: Sequence[Demand],
    ) -> Result[tuple[Flow, ...], str, Err[str]]:
        """优化流分配 / Optimize flow allocation.

        按优先级降序处理每个需求：寻找最短路径，推送流量，
        更新残余容量，直至所有需求处理完毕。
        Processes each demand in descending priority order:
        finds the shortest path, pushes flow, updates residual
        capacities, until all demands are processed.

        Args:
            nodes: 网络中的所有节点 / All nodes in the network.
            edges: 网络中的所有边 / All edges in the network.
            demands: 所有流量需求 / All flow demands.

        Returns:
            成功时返回分配的流元组，失败时返回错误。
            On success, a tuple of allocated flows.
            On failure, an error describing what went wrong.
        """
        if not demands:
            return Ok(())

        # 按优先级降序排列 / Sort by descending priority
        sorted_demands = sorted(demands, key=lambda d: d.priority, reverse=True)

        # 残余容量表: edge_key -> remaining capacity /
        # Residual capacity table: edge_key -> remaining
        residual: dict[str, float] = {}
        for edge in edges:
            residual[edge.edge_key] = edge.capacity

        # 构建边查找表 / Build edge lookup
        edge_map: dict[str, Edge] = {e.edge_key: e for e in edges}

        # 按节点键构建入边和出边索引 /
        # Build in-edge and out-edge indices by node key
        out_edges: dict[str, list[Edge]] = defaultdict(list)
        for edge in edges:
            out_edges[edge.from_node_key].append(edge)

        all_flows: list[Flow] = []
        flow_counter = 0

        for demand in sorted_demands:
            remaining = demand.amount

            while remaining > 0.0:
                # 构建当前残余图的边列表 /
                # Build edge list for current residual graph
                active_edges = [
                    edge_map[ekey] for ekey, cap in residual.items() if cap > 0.0
                ]

                # 寻找最短路径 / Find shortest path
                path_result = ShortestPath.dijkstra(
                    nodes=nodes,
                    edges=active_edges,
                    source_key=demand.source_key,
                    sink_key=demand.sink_key,
                )

                if path_result.is_failed():
                    return path_result

                path = path_result.unwrap()

                # 计算路径上的瓶颈容量 /
                # Calculate bottleneck capacity on path
                bottleneck = remaining
                path_edges: list[Edge] = []
                for i in range(len(path) - 1):
                    from_key = path[i]
                    to_key = path[i + 1]
                    edge = FlowOptimizer._find_edge(
                        out_edges,
                        from_key,
                        to_key,
                    )
                    if edge is None:
                        return Failed(
                            Err(
                                _code=ErrorCode.NOT_FOUND,
                                _message=(
                                    f"路径边不存在 / "
                                    f"Path edge not found: "
                                    f"{from_key} -> {to_key}"
                                ),
                            )
                        )
                    path_edges.append(edge)
                    cap = residual.get(edge.edge_key, 0.0)
                    bottleneck = min(bottleneck, cap)

                if bottleneck <= 0.0:
                    return Failed(
                        Err(
                            _code=ErrorCode.RESOURCE_EXHAUSTED,
                            _message=(
                                f"路径容量不足 / "
                                f"Insufficient path capacity "
                                f"for demand "
                                f"{demand.demand_key}"
                            ),
                        )
                    )

                # 推送流量 / Push flow
                push_amount = min(bottleneck, remaining)

                # 计算路径代价 / Calculate path cost
                path_cost = sum(e.effective_cost(push_amount) for e in path_edges)

                flow_counter += 1
                all_flows.append(
                    Flow.create(
                        flow_key=(f"{demand.demand_key}_f{flow_counter}"),
                        edge_key=path_edges[0].edge_key,
                        amount=push_amount,
                        cost=path_cost,
                    )
                )

                # 更新残余容量 / Update residual capacities
                for edge in path_edges:
                    current_cap = residual.get(edge.edge_key, 0.0)
                    residual[edge.edge_key] = max(0.0, current_cap - push_amount)

                remaining -= push_amount

        return Ok(tuple(all_flows))

    @staticmethod
    def _find_edge(
        out_edges: dict[str, list[Edge]],
        from_key: str,
        to_key: str,
    ) -> Edge | None:
        """在出边列表中查找匹配的边。

        Find a matching edge in the outgoing edge list.

        Args:
            out_edges: 出边索引 / Out-edge index.
            from_key: 起始节点键 / Source node key.
            to_key: 终止节点键 / Target node key.

        Returns:
            匹配的边，未找到返回 None。
            The matching edge, or None if not found.
        """
        for edge in out_edges.get(from_key, []):
            if edge.to_node_key == to_key:
                return edge
        return None  # reason: no matching edge found
