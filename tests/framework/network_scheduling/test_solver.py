"""网络排程求解器测试。

Network scheduling solver tests:
shortest path, max flow, infeasible, unreachable.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.network_scheduling.domain.edge.model.edge import Edge
from ospf_python.framework.network_scheduling.domain.flow.model.demand import Demand
from ospf_python.framework.network_scheduling.domain.node.model.node import Node
from ospf_python.framework.network_scheduling.domain.node.model.node_type import (
    NodeType,
)
from ospf_python.framework.network_scheduling.domain.service.flow_optimizer import (
    FlowOptimizer,
)
from ospf_python.framework.network_scheduling.domain.service.shortest_path import (
    ShortestPath,
)


def _make_triangle_network() -> tuple[list[Node], list[Edge]]:
    """创建三角形网络。/ Create triangle network.

    A --1--> B --2--> C
    \\--------5--------/
    """
    nodes = [
        Node.create(node_key="A", name="Source", node_type=NodeType.SOURCE),
        Node.create(node_key="B", name="Transit", node_type=NodeType.TRANSIT),
        Node.create(node_key="C", name="Sink", node_type=NodeType.SINK),
    ]
    edges = [
        Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", capacity=10.0, cost=1.0),
        Edge.create(edge_key="e2", from_node_key="B", to_node_key="C", capacity=5.0, cost=2.0),
        Edge.create(edge_key="e3", from_node_key="A", to_node_key="C", capacity=8.0, cost=5.0),
    ]
    return nodes, edges


# ============================================================
# Shortest path
# ============================================================


class TestShortestPath:
    """最短路径测试。/ Shortest path tests."""

    def test_shortest_path_found(self) -> None:
        """找到最短路径。/ Shortest path found."""
        nodes, edges = _make_triangle_network()
        result = ShortestPath.dijkstra(nodes=nodes, edges=edges, source_key="A", sink_key="C")
        # A→B→C = 1+2=3, A→C = 5 → 最短路径为 A→B→C
        assert result.is_ok()
        path = result.unwrap()
        assert path == ("A", "B", "C")

    def test_shortest_path_direct(self) -> None:
        """直连路径。/ Direct path."""
        nodes = [
            Node.create(node_key="A", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="B", name="Sink", node_type=NodeType.SINK),
        ]
        edges = [
            Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", cost=3.0),
        ]
        result = ShortestPath.dijkstra(nodes=nodes, edges=edges, source_key="A", sink_key="B")
        assert result.is_ok()
        path = result.unwrap()
        assert path == ("A", "B")

    def test_unreachable_network(self) -> None:
        """不可达网络。/ Unreachable network."""
        nodes = [
            Node.create(node_key="A", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="B", name="Transit", node_type=NodeType.TRANSIT),
            Node.create(node_key="C", name="Sink", node_type=NodeType.SINK),
        ]
        edges = [
            Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", cost=1.0),
        ]
        # A→B 存在, 但 B→C 不存在, C 不可达
        result = ShortestPath.dijkstra(nodes=nodes, edges=edges, source_key="A", sink_key="C")
        assert result.is_failed()

    def test_source_not_found(self) -> None:
        """源节点不存在。/ Source node not found."""
        nodes, edges = _make_triangle_network()
        result = ShortestPath.dijkstra(nodes=nodes, edges=edges, source_key="X", sink_key="C")
        assert result.is_failed()

    def test_sink_not_found(self) -> None:
        """汇节点不存在。/ Sink node not found."""
        nodes, edges = _make_triangle_network()
        result = ShortestPath.dijkstra(nodes=nodes, edges=edges, source_key="A", sink_key="X")
        assert result.is_failed()

    def test_same_source_and_sink(self) -> None:
        """源汇相同时路径为单点。/ Path is single node when source equals sink."""
        nodes, edges = _make_triangle_network()
        result = ShortestPath.dijkstra(nodes=nodes, edges=edges, source_key="A", sink_key="A")
        assert result.is_ok()
        assert result.unwrap() == ("A",)


# ============================================================
# Flow optimizer
# ============================================================


class TestFlowOptimizer:
    """最大流测试。/ Max flow tests."""

    def test_flow_optimizer_single_demand(self) -> None:
        """单需求流优化。/ Single demand flow optimization."""
        nodes = [
            Node.create(node_key="A", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="B", name="Transit", node_type=NodeType.TRANSIT),
            Node.create(node_key="C", name="Sink", node_type=NodeType.SINK),
        ]
        edges = [
            Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", capacity=10.0, cost=1.0),
            Edge.create(edge_key="e2", from_node_key="B", to_node_key="C", capacity=5.0, cost=2.0),
        ]
        demands = [
            Demand.create(demand_key="d1", source_key="A", sink_key="C", amount=3.0),
        ]
        result = FlowOptimizer.optimize(nodes=nodes, edges=edges, demands=demands)
        assert result.is_ok()
        flows = result.unwrap()
        assert len(flows) > 0
        total_flow = sum(f.amount for f in flows)
        assert total_flow == pytest.approx(3.0)

    def test_max_flow_basic(self) -> None:
        """基本最大流。/ Basic max flow."""
        nodes = [
            Node.create(node_key="A", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="B", name="Transit", node_type=NodeType.TRANSIT),
            Node.create(node_key="C", name="Sink", node_type=NodeType.SINK),
        ]
        edges = [
            Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", capacity=10.0, cost=1.0),
            Edge.create(edge_key="e2", from_node_key="B", to_node_key="C", capacity=5.0, cost=2.0),
        ]
        demands = [
            Demand.create(demand_key="d1", source_key="A", sink_key="C", amount=5.0),
        ]
        result = FlowOptimizer.optimize(nodes=nodes, edges=edges, demands=demands)
        assert result.is_ok()
        flows = result.unwrap()
        total_flow = sum(f.amount for f in flows)
        # 瓶颈在 B→C (容量 5)，最大流 = 5
        assert total_flow == pytest.approx(5.0)

    def test_capacity_insufficient(self) -> None:
        """容量不足（不可行）。/ Capacity insufficient (infeasible)."""
        nodes = [
            Node.create(node_key="A", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="B", name="Transit", node_type=NodeType.TRANSIT),
            Node.create(node_key="C", name="Sink", node_type=NodeType.SINK),
        ]
        edges = [
            Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", capacity=2.0, cost=1.0),
            Edge.create(edge_key="e2", from_node_key="B", to_node_key="C", capacity=1.0, cost=1.0),
        ]
        demands = [
            Demand.create(demand_key="d1", source_key="A", sink_key="C", amount=5.0),
        ]
        result = FlowOptimizer.optimize(nodes=nodes, edges=edges, demands=demands)
        # 最大流受限于最小割 (1.0)，需求 5.0 无法满足
        assert result.is_failed()

    def test_empty_demands(self) -> None:
        """空需求列表。/ Empty demand list."""
        nodes, edges = _make_triangle_network()
        result = FlowOptimizer.optimize(nodes=nodes, edges=edges, demands=[])
        assert result.is_ok()
        assert result.unwrap() == ()

    def test_no_path_for_demand(self) -> None:
        """需求无可达路径。/ No path for demand."""
        nodes = [
            Node.create(node_key="A", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="B", name="Sink", node_type=NodeType.SINK),
        ]
        edges: list[Edge] = []  # 没有边
        demands = [
            Demand.create(demand_key="d1", source_key="A", sink_key="B", amount=1.0),
        ]
        result = FlowOptimizer.optimize(nodes=nodes, edges=edges, demands=demands)
        assert result.is_failed()

    def test_priority_ordering(self) -> None:
        """高优先级需求先分配。/ Higher priority demands allocated first."""
        nodes = [
            Node.create(node_key="A", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="B", name="Transit", node_type=NodeType.TRANSIT),
            Node.create(node_key="C", name="Sink", node_type=NodeType.SINK),
        ]
        edges = [
            Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", capacity=10.0, cost=1.0),
            Edge.create(edge_key="e2", from_node_key="B", to_node_key="C", capacity=3.0, cost=1.0),
        ]
        demands = [
            Demand.create(demand_key="d_low", source_key="A", sink_key="C", amount=1.0, priority=1),
            Demand.create(demand_key="d_high", source_key="A", sink_key="C", amount=3.0, priority=10),
        ]
        result = FlowOptimizer.optimize(nodes=nodes, edges=edges, demands=demands)
        # 高优先级先分配, 容量 3.0 全部给 d_high
        # d_low 需求 1.0, 但剩余容量为 0 → 失败
        assert result.is_failed()
